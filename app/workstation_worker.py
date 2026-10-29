import os

import httpx

from app.agent_planner import AgentPlanner
from app.agent_memory import AgentMemory
from app.workflow_dispatch import dispatch_workflow
from app.workflow_approvals import submit_workflow_approval


class WorkstationWorker:
    def __init__(self, base_url, token, transport=None):
        if not token:
            raise ValueError("Agent token required")

        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
        }
        self.transport = transport

    def request(self, method, path, **kwargs):
        with httpx.Client(
            base_url=self.base_url,
            headers=self.headers,
            transport=self.transport,
            timeout=15,
        ) as client:
            response = client.request(
                method, path, **kwargs
            )
            response.raise_for_status()
            return response.json()

    def run_once(self):
        self.request(
            "POST", "/api/agents/heartbeat"
        )

        data = self.request(
            "GET", "/api/workstation/jobs"
        )

        for job in data["jobs"]:
            if job["status"] != "queued":
                continue

            if job["kind"] not in {
                "lead:analyze",
                "lead:process",
            }:
                continue

            message = job["instructions"].get("message")

            if not isinstance(message, str):
                continue

            if not 1 <= len(message.strip()) <= 2000:
                continue

            job_id = job["id"]

            try:
                self.request(
                    "POST",
                    f"/api/workstation/jobs/{job_id}/claim",
                )
            except httpx.HTTPStatusError as error:
                if error.response.status_code == 409:
                    continue
                raise

            if job["kind"] == "lead:process":
                workflow = dispatch_workflow(
                    "lead:process",
                    {"message": message},
                )

                if workflow["status"] != "awaiting_approval":
                    raise RuntimeError(
                        "Workflow did not reach approval"
                    )

                proposal_id = submit_workflow_approval(
                    self, job, workflow
                )
                analysis = workflow["result"]
            else:
                state = AgentPlanner().execute(
                    "Analyze assigned lead",
                    {"message": message},
                )

                if state.status != "completed":
                    raise RuntimeError(
                        "Agent execution failed"
                    )

                analysis = state.result

            self.request(
                "POST",
                f"/api/workstation/jobs/{job_id}/complete",
                json={
                    "result": {
                        "worker": "Leadkeeper",
                        "analysis": analysis,
                        "requires_human_review": True,
                        "proposal_id": (
                            proposal_id
                            if job["kind"] == "lead:process"
                            else None
                        ),
                    }
                },
            )

            business_id = job.get("business_id")

            if isinstance(business_id, int) and business_id > 0:
                try:
                    AgentMemory().remember(
                        business_id=business_id,
                        objective="Analyze assigned lead",
                        status="completed",
                        result={
                            "job_id": job_id,
                            "analysis": analysis,
                        },
                    )
                except Exception:
                    # The business job is already completed.
                    # Memory failure must not trigger another execution.
                    pass

            return {
                "job_id": job_id,
                "status": "completed",
                "analysis": analysis,
            }

        return {"status": "idle"}


def main():
    worker = WorkstationWorker(
        base_url=os.getenv(
            "GNOMEBUSINESS_URL",
            "http://127.0.0.1:8000",
        ),
        token=os.environ["GNOME_AGENT_TOKEN"],
    )

    print(worker.run_once())


if __name__ == "__main__":
    main()

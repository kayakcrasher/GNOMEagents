import os

import httpx

from app.agent_tools import build_runtime


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
        data = self.request(
            "GET", "/api/workstation/jobs"
        )

        for job in data["jobs"]:
            if job["status"] != "queued":
                continue

            if job["kind"] != "lead:analyze":
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

            state = build_runtime().run(
                objective="Analyze assigned lead",
                plan=[{
                    "tool": "lead.analyze",
                    "args": {"message": message},
                }],
            )

            if state.status != "completed":
                raise RuntimeError(
                    "Agent execution failed"
                )

            self.request(
                "POST",
                f"/api/workstation/jobs/{job_id}/complete",
                json={
                    "result": {
                        "worker": "Leadkeeper",
                        "analysis": state.result,
                        "requires_human_review": True,
                    }
                },
            )

            return {
                "job_id": job_id,
                "status": "completed",
                "analysis": state.result,
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

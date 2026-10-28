import httpx

from app.pilot_pipeline import process_inquiry


class ApprovalBridge:
    def __init__(self, base_url, token, transport=None):
        if not token:
            raise ValueError("Agent token required")

        self.base_url = base_url.rstrip("/")
        self.token = token
        self.transport = transport

    def submit(self, name, message):
        result = process_inquiry(name, message)

        if result.status != "awaiting_approval":
            return {
                "status": "blocked",
                "reason": "draft_not_ready",
            }

        proposal = {
            "action": "outreach:draft",
            "title": "Leadkeeper response review",
            "payload": {
                "customer_name": name,
                "inquiry": message,
                "analysis": result.analysis,
                "draft": result.draft,
                "evaluation": result.evaluation,
                "requires_human_approval": True,
            },
        }

        with httpx.Client(
            base_url=self.base_url,
            transport=self.transport,
            timeout=15,
        ) as client:
            response = client.post(
                "/api/approvals/proposals",
                headers={
                    "Authorization": f"Bearer {self.token}",
                },
                json=proposal,
            )
            response.raise_for_status()
            saved = response.json()

        return {
            "status": "pending",
            "proposal_id": saved["id"],
            "executed": False,
        }

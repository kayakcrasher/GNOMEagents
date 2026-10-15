from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class KnowledgeResult:
    question: str
    collection_id: str
    answer: str
    facts: list[dict]
    evidence: list[dict]
    online_used: bool


class GNOMEdataClient:
    """HTTP bridge from GNOME Agents to GNOMEdata."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8001",
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def query(
        self,
        question: str,
        collection_id: str = "default",
    ) -> KnowledgeResult:
        response = httpx.post(
            f"{self.base_url}/api/query",
            json={
                "question": question,
                "collection_id": collection_id,
                "allow_online": False,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()
        data = response.json()

        return KnowledgeResult(
            question=data["question"],
            collection_id=data["collection_id"],
            answer=data["answer"],
            facts=data["facts"],
            evidence=data["evidence"],
            online_used=data["online_used"],
        )

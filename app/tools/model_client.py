"""OpenAI-compatible inference adapter for GNOMEagents."""

import json
import os
import urllib.error
import urllib.request

from app.tools.registry import ToolError


SYSTEM_PROMPT = """
You are GNOME Codekeeper, an autonomous Python
repository investigation agent.

Your job is to investigate coding objectives using
the available workspace tools.

Return exactly one JSON object per decision.

Tool decision:
{
  "action": "tool",
  "name": "files.list",
  "arguments": {"path": "."}
}

Finish decision:
{
  "action": "finish",
  "result": {
    "summary": "What you discovered",
    "findings": ["Evidence-based finding"],
    "recommendation": "Next action"
  }
}

Rules:
- Only request tools listed in available_tools.
- Use observations as evidence.
- Never invent file contents or test results.
- Inspect relevant files before drawing conclusions.
- Do not repeat failed tool calls without a reason.
- Never claim code was modified or verified unless
  observations prove it.
- Use files.list ONLY for directories.
- Use files.read ONLY for files.
- Paths ending in .py or .md are normally files, not directories.
- Never repeat a tool call already attempted, whether it succeeded or failed.
- When the requested file has been read, finish with a concise evidence-based answer.
- If the evidence is insufficient, say what is unknown instead of repeating tools.
- Finish when investigation is sufficient.
- Return JSON only, without markdown fences.
"""


class ModelClient:
    def __init__(
        self,
        base_url=None,
        model=None,
        api_key=None,
        timeout=180,
    ):
        self.base_url = (
            base_url
            or os.environ.get(
                "GNOME_MODEL_URL",
                "http://127.0.0.1:11434/v1",
            )
        ).rstrip("/")

        self.model = (
            model
            or os.environ.get(
                "GNOME_MODEL_NAME",
                "qwen2.5-coder:7b",
            )
        )

        self.api_key = (
            api_key
            if api_key is not None
            else os.environ.get(
                "GNOME_MODEL_KEY", ""
            )
        )

        self.timeout = timeout

    def decide(self, request):
        payload = {
            "model": self.model,
            "temperature": 0,
            "max_tokens": 256,
            "response_format": {
                "type": "json_object"
            },
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(request),
                },
            ],
        }

        data = json.dumps(payload).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = (
                f"Bearer {self.api_key}"
            )

        http_request = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=data,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                http_request,
                timeout=self.timeout,
            ) as response:
                result = json.load(response)

        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
            ValueError,
        ) as error:
            raise ToolError(
                "Model connection or response failed"
            ) from error

        try:
            content = result["choices"][0][
                "message"
            ]["content"]

            if not isinstance(content, str):
                raise ValueError("Invalid content")

            content = content.strip()

            if content.startswith("```"):
                lines = content.splitlines()
                if len(lines) >= 3 and lines[-1].strip() == "```":
                    content = "\n".join(lines[1:-1])

            decision = json.loads(content)

            if not isinstance(decision, dict):
                raise ValueError("Decision must be object")

            return decision

        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            raise ToolError(
                "Model returned invalid decision JSON"
            ) from error

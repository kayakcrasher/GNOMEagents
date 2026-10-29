"""Verify the local model requests structured JSON."""

import io
import json
from unittest.mock import patch

from app.tools.model_client import ModelClient


class FakeResponse:
    def __enter__(self):
        return io.BytesIO(
            json.dumps({
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "action": "finish",
                            "result": {
                                "summary": "Inspection complete"
                            },
                        })
                    }
                }]
            }).encode()
        )

    def __exit__(self, *args):
        return False


def test_model_requests_json_mode():
    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse()

    with patch(
        "urllib.request.urlopen",
        side_effect=fake_urlopen,
    ):
        decision = ModelClient(
            base_url="http://127.0.0.1:8080/v1",
            model="test-model",
        ).decide({"objective": "Inspect README.md"})

    assert captured["payload"]["response_format"] == {
        "type": "json_object"
    }
    assert captured["payload"]["max_tokens"] == 256
    assert decision["action"] == "finish"

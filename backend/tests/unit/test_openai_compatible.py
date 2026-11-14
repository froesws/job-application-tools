"""The OpenAI-compatible adapter talks to any compatible endpoint over stdlib urllib."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import ClassVar

import pytest
from cvtailor.llm.client import LLMError, TransientLLMError
from cvtailor.llm.openai_compatible import OpenAICompatibleClient


class Stub(BaseHTTPRequestHandler):
    status: ClassVar[int] = 200
    body: ClassVar[dict[str, object]] = {}
    received: ClassVar[dict[str, object]] = {}

    def do_POST(self) -> None:
        length = int(self.headers["content-length"])
        Stub.received = {
            "path": self.path,
            "authorization": self.headers.get("authorization"),
            "payload": json.loads(self.rfile.read(length)),
        }
        encoded = json.dumps(self.body).encode("utf-8")
        self.send_response(Stub.status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, *args: object) -> None:
        return


@pytest.fixture()
def stub() -> Iterator[str]:
    Stub.status = 200
    Stub.body = {"choices": [{"message": {"content": '{"ok": true}'}}]}
    server = HTTPServer(("127.0.0.1", 0), Stub)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/v1"
    finally:
        server.shutdown()
        thread.join()


def test_the_adapter_reads_the_first_choice(stub: str) -> None:
    client = OpenAICompatibleClient(provider="openai", key="secret", base_url=stub)

    assert client.complete("hello", model="gpt") == '{"ok": true}'


def test_the_adapter_sends_the_key_and_the_model(stub: str) -> None:
    client = OpenAICompatibleClient(provider="openai", key="secret", base_url=stub)

    client.complete("hello", model="gpt")

    assert Stub.received["authorization"] == "Bearer secret"
    payload = Stub.received["payload"]
    assert payload["model"] == "gpt"
    assert payload["messages"] == [{"role": "user", "content": "hello"}]
    assert Stub.received["path"] == "/v1/chat/completions"


def test_a_server_error_is_transient(stub: str) -> None:
    Stub.status = 503
    client = OpenAICompatibleClient(provider="openai", key="secret", base_url=stub)

    with pytest.raises(TransientLLMError):
        client.complete("hello", model="gpt")


def test_a_client_error_is_not_transient(stub: str) -> None:
    Stub.status = 400
    client = OpenAICompatibleClient(provider="openai", key="secret", base_url=stub)

    with pytest.raises(LLMError) as caught:
        client.complete("hello", model="gpt")

    assert not isinstance(caught.value, TransientLLMError)

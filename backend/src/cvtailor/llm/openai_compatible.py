"""The OpenAI-compatible adapter.

It uses the standard library on purpose: the LLM interface must stay dependency-free, and
every provider worth using in this project speaks this shape.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from cvtailor.llm.client import LLMError, TransientLLMError

_TRANSIENT_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


class OpenAICompatibleClient:
    def __init__(
        self,
        *,
        provider: str,
        key: str,
        base_url: str,
        timeout_s: float = 60.0,
    ) -> None:
        self.provider = provider
        self._key = key
        self._base_url = base_url.rstrip("/")
        self._timeout_s = timeout_s

    def complete(self, prompt: str, *, model: str) -> str:
        payload = {
            "model": model,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        }
        request = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "authorization": f"Bearer {self._key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_s) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            raise _from_http(error) from error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise TransientLLMError(f"{self.provider} is unreachable: {error}") from error
        except json.JSONDecodeError as error:
            raise LLMError(f"{self.provider} returned malformed JSON") from error
        return _content(body, self.provider)


def _from_http(error: urllib.error.HTTPError) -> LLMError:
    message = f"HTTP {error.code}"
    if error.code in _TRANSIENT_STATUS:
        return TransientLLMError(message)
    return LLMError(message)


def _content(body: Any, provider: str) -> str:
    try:
        return str(body["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as error:
        raise LLMError(f"{provider} returned an unexpected payload") from error

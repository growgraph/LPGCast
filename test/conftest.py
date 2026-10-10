"""Shared fixtures: an isolated environment and a scripted OpenAI-compatible endpoint."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest

from lpgcast.config import CacheSettings, LLMSettings
from lpgcast.llm import LLMCache, LLMClient

DATA = Path(__file__).parent / "data"

_SHELL_VARS = (
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_ORG_ID",
    "OPENAI_PROJECT_ID",
)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-llm", action="store_true", help="run tests that call a real model"
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--run-llm"):
        return
    skip = pytest.mark.skip(reason="needs --run-llm")
    for item in items:
        if "llm" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """No setting from the developer's shell, a cache per test, and no backoff sleeps."""
    for name in list(os.environ):
        if name.startswith("LPGCAST_") or name in _SHELL_VARS:
            monkeypatch.delenv(name)
    monkeypatch.setenv("LPGCAST_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setattr("lpgcast.llm.client.RETRY_BACKOFF_BASE_SECONDS", 0.0)


def completion(content: str, *, model: str = "fake-model", **usage: Any) -> dict:
    """An OpenAI chat-completion body carrying *content*."""
    return {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 0,
        "model": model,
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": content},
            }
        ],
        "usage": {
            "prompt_tokens": usage.get("prompt_tokens", 10),
            "completion_tokens": usage.get("completion_tokens", 5),
            "total_tokens": usage.get("prompt_tokens", 10)
            + usage.get("completion_tokens", 5),
            "prompt_tokens_details": {"cached_tokens": usage.get("cached_tokens", 0)},
        },
    }


def error(status: int, message: str, code: str | None = None) -> httpx.Response:
    """An OpenAI-shaped error response."""
    return httpx.Response(
        status,
        json={
            "error": {"message": message, "type": "invalid_request_error", "code": code}
        },
    )


Reply = str | dict | httpx.Response | Exception


class FakeEndpoint:
    """Replays scripted replies in order and records every request body.

    A ``dict`` reply is sent as JSON content, a ``str`` as raw content, an
    ``httpx.Response`` as is, and an exception is raised by the transport.
    """

    def __init__(self, replies: list[Reply]) -> None:
        self.replies = list(replies)
        self.requests: list[dict[str, Any]] = []
        self.http_client = httpx.AsyncClient(
            transport=httpx.MockTransport(self._handle)
        )

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(json.loads(request.content))
        if not self.replies:
            return error(500, "no scripted reply left")
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, httpx.Response):
            return reply
        content = reply if isinstance(reply, str) else json.dumps(reply)
        return httpx.Response(200, json=completion(content))


@pytest.fixture
def llm_settings() -> LLMSettings:
    return LLMSettings(
        model="fake-model",
        api_key="test-key",
        base_url="http://fake.local/v1",
        transport_retries=0,
    )


@pytest.fixture
def make_client(
    llm_settings: LLMSettings,
) -> Callable[..., tuple[LLMClient, FakeEndpoint]]:
    """Build a client wired to a :class:`FakeEndpoint` scripted with *replies*."""

    def _build(
        *replies: Reply,
        settings: LLMSettings | None = None,
        cache: CacheSettings | None = None,
        **overrides: Any,
    ) -> tuple[LLMClient, FakeEndpoint]:
        endpoint = FakeEndpoint(list(replies))
        base = settings or llm_settings
        if overrides:
            base = base.model_copy(update=overrides)
        client = LLMClient(base, LLMCache(cache), http_client=endpoint.http_client)
        return client, endpoint

    return _build


SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
    "additionalProperties": False,
}
MESSAGES = [
    {"role": "system", "content": "You extract."},
    {"role": "user", "content": "Ann runs press 7."},
]

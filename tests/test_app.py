"""Hosted authentication, validation and debate routing."""

from __future__ import annotations

from types import SimpleNamespace
from urllib.error import HTTPError

from fastapi.testclient import TestClient

import app as web_app


def test_hosted_debate_requires_login_and_origin(monkeypatch):
    def auth(method, path, *, token="", body=None):
        if path == "user" and token == "access":
            return {"id": "user-1", "email": "user@example.com"}
        if path == "token?grant_type=password":
            return {
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_in": 3600,
            }
        raise AssertionError((method, path))

    class FakeDebate:
        def __init__(self, agents, judge):
            assert set(agents) == {"pragmatic-architect", "critical-reviewer"}

        def run(self, question):
            assert question == "Choose pagination"
            return SimpleNamespace(answer="Use cursor pagination", consensus=1.0)

    monkeypatch.setattr(web_app, "_auth_request", auth)
    monkeypatch.setattr(web_app.OpenAICompatibleLLM, "from_env", lambda: object())
    monkeypatch.setattr(web_app, "Debate", FakeDebate)
    client = TestClient(web_app.app, base_url="https://debate.example.com")
    payload = {"action": "debate", "values": {"question": "Choose pagination"}}
    assert (
        client.post(
            "/api/action",
            json=payload,
            headers={"Origin": "https://debate.example.com"},
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "password123"},
            headers={"Origin": "https://evil.example.com"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "password123"},
            headers={"Origin": "https://debate.example.com"},
        ).status_code
        == 200
    )
    response = client.post(
        "/api/action", json=payload, headers={"Origin": "https://debate.example.com"}
    )
    assert response.json()["result"]["answer"] == "Use cursor pagination"
    assert (
        client.post(
            "/api/action",
            json={"action": "debate", "values": {"question": "x" * 2001}},
            headers={"Origin": "https://debate.example.com"},
        ).status_code
        == 400
    )

    def provider_down(question):
        raise HTTPError("https://model.example", 403, "blocked", {}, None)

    monkeypatch.setattr(
        FakeDebate, "run", lambda self, question: provider_down(question)
    )
    assert (
        client.post(
            "/api/action",
            json=payload,
            headers={"Origin": "https://debate.example.com"},
        ).status_code
        == 503
    )

    def rate_limited(question):
        raise HTTPError("https://model.example", 429, "limited", {}, None)

    monkeypatch.setattr(
        FakeDebate, "run", lambda self, question: rate_limited(question)
    )
    assert (
        client.post(
            "/api/action",
            json=payload,
            headers={"Origin": "https://debate.example.com"},
        ).status_code
        == 429
    )

"""Check hosted sign-in and a real debate, then remove the temporary account."""

from __future__ import annotations

import os
import secrets

import httpx


def main() -> None:
    base = os.environ["SUPABASE_URL"].rstrip("/")
    hosted = os.environ.get(
        "HOSTED_URL", "https://multi-agent-debate-one.vercel.app"
    ).rstrip("/")
    secret = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {"apikey": secret, "Authorization": f"Bearer {secret}"}
    email = f"agent-debate-smoke-{secrets.token_hex(8)}@example.com"
    password = secrets.token_urlsafe(24)
    user_id = None
    with httpx.Client(timeout=90.0) as client:
        try:
            created = client.post(
                f"{base}/auth/v1/admin/users",
                headers=headers,
                json={"email": email, "password": password, "email_confirm": True},
            )
            created.raise_for_status()
            user_id = created.json()["id"]
            assert client.get(f"{hosted}/api/session").status_code == 401
            login = client.post(
                f"{hosted}/auth/login",
                headers={"Origin": hosted},
                json={"email": email, "password": password},
            )
            login.raise_for_status()
            assert client.get(f"{hosted}/api/session").json()["id"] == user_id
            result = client.post(
                f"{hosted}/api/action",
                headers={"Origin": hosted},
                json={
                    "action": "debate",
                    "values": {
                        "question": "Should a small API use cursor pagination for a changing feed?"
                    },
                },
            )
            result.raise_for_status()
            data = result.json()["result"]
            assert data["answer"].strip()
            assert len(data["proposals"]) == 2
            assert len(data["critiques"]) == 2
            assert len(data["votes"]) == 2
            assert 0 <= data["consensus"] <= 1
            logout = client.post(
                f"{hosted}/auth/logout", headers={"Origin": hosted}, json={}
            )
            logout.raise_for_status()
            assert client.get(f"{hosted}/api/session").status_code == 401
            print("Hosted sign-in, debate, and sign-out passed")
        finally:
            if user_id:
                deleted = client.delete(
                    f"{base}/auth/v1/admin/users/{user_id}", headers=headers
                )
                deleted.raise_for_status()


if __name__ == "__main__":
    main()

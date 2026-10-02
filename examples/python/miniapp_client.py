"""Minimal Python client for the Svoi Pravila Mini App API (/v1/miniapp).

Usage against a running backend (see docs/QUICKSTART.md):

    set TELEGRAM_BOT_TOKEN=123456:TEST_TOKEN     # same token the backend uses
    python examples/python/miniapp_client.py --base-url http://localhost:8000

Every request is authenticated with the raw Telegram ``initData`` string in the
``X-Telegram-Init-Data`` header. The backend derives the user from validated
initData only; clients never send ``user_id``.

``sign_init_data`` produces a valid initData for LOCAL DEVELOPMENT ONLY. Real
Mini Apps must forward ``Telegram.WebApp.initData`` unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import time
from typing import Any
from urllib.parse import urlencode

import httpx

MINIAPP_PREFIX = "/v1/miniapp"
INIT_DATA_HEADER = "X-Telegram-Init-Data"


class MiniAppApiError(Exception):
    def __init__(self, status: int, detail: Any) -> None:
        super().__init__(f"{status}: {detail}")
        self.status = status
        self.detail = detail


def sign_init_data(
    bot_token: str,
    *,
    telegram_user_id: int = 777001,
    first_name: str = "Dev",
    language_code: str = "ru",
    auth_date: int | None = None,
) -> str:
    """Build a correctly signed initData string (local development only)."""
    values = {
        "auth_date": str(int(time.time()) if auth_date is None else auth_date),
        "query_id": "local-dev",
        "user": json.dumps(
            {"id": telegram_user_id, "first_name": first_name, "language_code": language_code},
            separators=(",", ":"),
            ensure_ascii=False,
        ),
    }
    data_check_string = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(values)


class MiniAppClient:
    def __init__(
        self,
        base_url: str,
        init_data: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._http = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={INIT_DATA_HEADER: init_data},
            transport=transport,
            timeout=timeout,
        )

    async def __aenter__(self) -> "MiniAppClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._http.aclose()

    async def _request(self, method: str, path: str, body: Any = None) -> Any:
        response = await self._http.request(method, f"{MINIAPP_PREFIX}{path}", json=body)
        if response.status_code == 204:
            return None
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if response.is_error:
            detail = payload.get("detail") if isinstance(payload, dict) else None
            raise MiniAppApiError(response.status_code, detail or "Request failed")
        return payload

    async def auth(self) -> dict[str, Any]:
        return await self._request("POST", "/auth")

    async def bootstrap(self) -> dict[str, Any]:
        return await self._request("GET", "/bootstrap")

    async def list_relationships(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/relationships")

    async def create_relationship(self, **body: Any) -> dict[str, Any]:
        return await self._request("POST", "/relationships", body)

    async def update_relationship(self, relationship_id: str, **body: Any) -> dict[str, Any]:
        return await self._request("PATCH", f"/relationships/{relationship_id}", body)

    async def delete_relationship(self, relationship_id: str) -> None:
        await self._request("DELETE", f"/relationships/{relationship_id}")

    async def set_default_relationship(self, relationship_id: str) -> dict[str, Any]:
        return await self._request("PUT", f"/me/default-relationship/{relationship_id}")

    async def add_rule(self, relationship_id: str, *, type: str, value: str, priority: int = 0) -> dict[str, Any]:
        body = {"type": type, "value": value, "priority": priority}
        return await self._request("POST", f"/relationships/{relationship_id}/rules", body)

    async def update_rule(
        self, relationship_id: str, rule_id: int, *, type: str, value: str, priority: int = 0
    ) -> dict[str, Any]:
        body = {"type": type, "value": value, "priority": priority}
        return await self._request("PUT", f"/relationships/{relationship_id}/rules/{rule_id}", body)

    async def delete_rule(self, relationship_id: str, rule_id: int) -> None:
        await self._request("DELETE", f"/relationships/{relationship_id}/rules/{rule_id}")

    async def assist(
        self, workflow: str, text: str, *, relationship_id: str | None = None, language: str | None = None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"text": text}
        if relationship_id is not None:
            body["relationship_id"] = relationship_id
        if language is not None:
            body["language"] = language
        return await self._request("POST", f"/assist/{workflow}", body)


async def run_scenario(client: MiniAppClient) -> dict[str, Any]:
    """auth -> create relationship -> add rule -> bootstrap -> soften."""
    auth = await client.auth()
    relationship = await client.create_relationship(
        relation_type="spouse", aliases=["Аня"], communication_style={"firmness": "direct"}, set_as_default=True
    )
    rule = await client.add_rule(
        relationship["relationship_id"], type="avoid", value="не использовать фразу 'ты всегда'", priority=100
    )
    bootstrap = await client.bootstrap()
    delivery = await client.assist("soften", "Ты всегда откладываешь дела!", language="ru")
    return {"auth": auth, "relationship": relationship, "rule": rule, "bootstrap": bootstrap, "delivery": delivery}


async def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default=os.environ.get("API_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--init-data", default=os.environ.get("TELEGRAM_INIT_DATA"))
    args = parser.parse_args()

    init_data = args.init_data
    if not init_data:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            raise SystemExit("Set TELEGRAM_INIT_DATA, or TELEGRAM_BOT_TOKEN to sign a local dev initData.")
        init_data = sign_init_data(token)

    async with MiniAppClient(args.base_url, init_data) as client:
        result = await run_scenario(client)
    delivery = result["delivery"]
    print(f"user_id={result['auth']['user']['user_id']} relationship_id={result['relationship']['relationship_id']}")
    print(f"assist status={delivery['status']} workflow={delivery['workflow']}")
    print(delivery["text"])


if __name__ == "__main__":
    import asyncio

    asyncio.run(_main())

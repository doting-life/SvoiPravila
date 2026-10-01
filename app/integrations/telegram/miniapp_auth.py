from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl

from pydantic import BaseModel, ConfigDict, Field


class TelegramInitDataError(ValueError):
    pass


class TelegramWebAppUser(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None
    allows_write_to_pm: bool | None = None
    photo_url: str | None = None


class TelegramInitData(BaseModel):
    model_config = ConfigDict(extra="allow")

    auth_date: int
    query_id: str | None = None
    user: TelegramWebAppUser
    start_param: str | None = None
    chat_type: str | None = None
    chat_instance: str | None = None


@dataclass(slots=True)
class TelegramMiniAppAuth:
    bot_token: str
    max_age_seconds: int = 3600

    def validate(self, raw_init_data: str, *, now: int | None = None) -> TelegramInitData:
        if not raw_init_data:
            raise TelegramInitDataError("Missing Telegram Mini App initData")

        parsed_pairs = parse_qsl(raw_init_data, keep_blank_values=True, strict_parsing=False)
        pairs: dict[str, str] = {}
        for key, value in parsed_pairs:
            if key in pairs:
                raise TelegramInitDataError(f"Duplicate Telegram initData field: {key}")
            pairs[key] = value
        received_hash = pairs.pop("hash", None)
        if not received_hash:
            raise TelegramInitDataError("Telegram initData has no hash")

        # Telegram's server-side Mini App validation contract:
        # secret_key = HMAC-SHA256(key="WebAppData", msg=bot_token)
        # signature  = HMAC-SHA256(key=secret_key, msg=data_check_string)
        data_check_string = "\n".join(f"{key}={pairs[key]}" for key in sorted(pairs))
        secret_key = hmac.new(b"WebAppData", self.bot_token.encode("utf-8"), hashlib.sha256).digest()
        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(received_hash, expected_hash):
            raise TelegramInitDataError("Invalid Telegram initData signature")

        auth_date_raw = pairs.get("auth_date")
        if auth_date_raw is None:
            raise TelegramInitDataError("Telegram initData has no auth_date")
        try:
            auth_date = int(auth_date_raw)
        except ValueError as exc:
            raise TelegramInitDataError("Invalid Telegram initData auth_date") from exc

        current = int(time.time()) if now is None else now
        age = current - auth_date
        if age < -30:
            raise TelegramInitDataError("Telegram initData auth_date is in the future")
        if self.max_age_seconds > 0 and age > self.max_age_seconds:
            raise TelegramInitDataError("Telegram initData has expired")

        raw_user = pairs.get("user")
        if not raw_user:
            raise TelegramInitDataError("Telegram initData has no user")
        try:
            user = json.loads(raw_user)
        except json.JSONDecodeError as exc:
            raise TelegramInitDataError("Telegram initData user is not valid JSON") from exc

        payload: dict[str, Any] = {
            "auth_date": auth_date,
            "query_id": pairs.get("query_id"),
            "user": user,
            "start_param": pairs.get("start_param"),
            "chat_type": pairs.get("chat_type"),
            "chat_instance": pairs.get("chat_instance"),
        }
        return TelegramInitData.model_validate(payload)

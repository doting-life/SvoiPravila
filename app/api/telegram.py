from __future__ import annotations

import hashlib
import hmac
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from app.artifacts import AssistRequest, WorkflowName
from app.integrations.telegram import TelegramWebAppUser, parse_inline_query, parse_message_command


router = APIRouter(prefix="/v1/telegram", tags=["telegram"])


def _workflow_title(workflow: WorkflowName) -> str:
    return {
        WorkflowName.SOFTEN: "Смягчить",
        WorkflowName.DECODE: "Расшифровать",
        WorkflowName.HELP_SAY: "Помоги сказать",
    }[workflow]


def _telegram_text(text: str) -> str:
    return text if len(text) <= 4096 else text[:4093] + "..."


def _inline_result(*, query_id: str, workflow: WorkflowName, text: str) -> dict[str, Any]:
    text = _telegram_text(text)
    stable_id = hashlib.sha256(f"{query_id}:{workflow.value}".encode("utf-8")).hexdigest()[:32]
    return {
        "type": "article",
        "id": stable_id,
        "title": _workflow_title(workflow),
        "description": text[:120],
        "input_message_content": {"message_text": text},
    }


async def _resolve_internal_user(container: Any, sender: dict[str, Any]):
    telegram_user = TelegramWebAppUser.model_validate(sender)
    return await container.users.get_or_create_from_telegram(telegram_user)


async def _handle_update(container: Any, settings: Any, update: dict[str, Any]) -> None:
    telegram = container.telegram
    if telegram is None:
        return

    inline = update.get("inline_query")
    if isinstance(inline, dict):
        query_id = str(inline.get("id", ""))
        query_text = str(inline.get("query", ""))
        sender = inline.get("from") or {}
        default = WorkflowName(settings.telegram_default_workflow)
        parsed = parse_inline_query(query_text, default)

        if not parsed.text:
            hints = [
                _inline_result(query_id=query_id, workflow=WorkflowName.SOFTEN, text="soften: текст сообщения"),
                _inline_result(query_id=query_id, workflow=WorkflowName.DECODE, text="decode: сообщение собеседника"),
                _inline_result(query_id=query_id, workflow=WorkflowName.HELP_SAY, text="скажи: что вы хотите донести"),
            ]
            await telegram.answer_inline_query(inline_query_id=query_id, results=hints)
            return

        try:
            user = await _resolve_internal_user(container, sender)
            delivery = await container.engine.execute(
                parsed.workflow,
                AssistRequest(
                    user_id=user.user_id,
                    text=parsed.text,
                    language=user.language_code or "ru",
                ),
            )
            results = [_inline_result(query_id=query_id, workflow=parsed.workflow, text=delivery.text)]
        except Exception:
            results = [_inline_result(
                query_id=query_id,
                workflow=parsed.workflow,
                text="Не удалось обработать запрос. Попробуйте ещё раз.",
            )]
        await telegram.answer_inline_query(inline_query_id=query_id, results=results)
        return

    message = update.get("message")
    if isinstance(message, dict) and isinstance(message.get("text"), str):
        sender = message.get("from") or {}
        chat = message.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            return
        default = WorkflowName(settings.telegram_default_workflow)
        parsed = parse_message_command(message["text"], default)
        if not parsed.text:
            await telegram.send_message(
                chat_id=chat_id,
                text="Напишите /soften, /decode или /say и затем текст.",
            )
            return
        try:
            user = await _resolve_internal_user(container, sender)
            delivery = await container.engine.execute(
                parsed.workflow,
                AssistRequest(
                    user_id=user.user_id,
                    text=parsed.text,
                    language=user.language_code or "ru",
                ),
            )
            text = delivery.text
        except Exception:
            text = "Не удалось обработать запрос. Попробуйте ещё раз."
        await telegram.send_message(chat_id=chat_id, text=text)


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, bool]:
    container = request.app.state.container
    settings = request.app.state.settings
    if not settings.telegram_enabled or container.telegram is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram adapter is disabled")

    expected = settings.telegram_webhook_secret.get_secret_value() if settings.telegram_webhook_secret else None
    if expected:
        received = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not hmac.compare_digest(received, expected):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram webhook secret")

    update = await request.json()
    background_tasks.add_task(_handle_update, container, settings, update)
    return {"ok": True}

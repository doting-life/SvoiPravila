from __future__ import annotations

import json
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from app.artifacts import SoftenResult
from app.container import build_llm_provider
from app.settings import AppSettings
from app.tools.llm import (
    DeepSeekStructuredLLMProvider,
    FakeStructuredLLMProvider,
    GigaChatStructuredLLMProvider,
    LLMGenerateTool,
    OpenAIStructuredLLMProvider,
)
from app.tools.llm.base import StructuredGenerationRequest

SECRET_KEY = "secret-authorization-key"
SECRET_TOKEN = "secret-access-token"
PRIVATE_TEXT = "private user text"


def _settings(**overrides) -> AppSettings:
    return AppSettings(_env_file=None, **overrides)


def _request() -> StructuredGenerationRequest:
    return StructuredGenerationRequest(
        system_instructions="system rules",
        user_payload={"message_request": {"text": PRIVATE_TEXT}},
        output_model=SoftenResult,
        metadata={"workflow": "soften"},
    )


def _soften_payload() -> dict:
    return {
        "request_id": str(uuid4()),
        "original_intent": "intent",
        "rewritten_message": "soft message",
        "tone_applied": "calm",
        "constraints_respected": [],
    }


# --------------------------------------------------------------------- settings


@pytest.mark.parametrize(
    ("provider", "overrides", "message"),
    [
        ("gigachat", {"gigachat_model": "GigaChat-2-Max"}, "GIGACHAT_CREDENTIALS"),
        ("gigachat", {"gigachat_credentials": SECRET_KEY}, "GIGACHAT_MODEL"),
        ("deepseek", {"deepseek_model": "deepseek-chat"}, "DEEPSEEK_API_KEY"),
        ("deepseek", {"deepseek_api_key": SECRET_KEY}, "DEEPSEEK_MODEL"),
    ],
)
def test_settings_require_provider_credentials_and_model(provider, overrides, message) -> None:
    with pytest.raises(ValueError, match=message):
        _settings(llm_provider=provider, **overrides)


def test_settings_default_remains_fake() -> None:
    assert _settings().llm_provider == "fake"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"llm_provider": "fake"}, FakeStructuredLLMProvider),
        ({"llm_provider": "openai", "openai_api_key": "k", "openai_model": "m"}, OpenAIStructuredLLMProvider),
        (
            {"llm_provider": "gigachat", "gigachat_credentials": SECRET_KEY, "gigachat_model": "GigaChat"},
            GigaChatStructuredLLMProvider,
        ),
        (
            {"llm_provider": "deepseek", "deepseek_api_key": SECRET_KEY, "deepseek_model": "deepseek-chat"},
            DeepSeekStructuredLLMProvider,
        ),
    ],
)
async def test_build_llm_provider_selects_configured_provider(overrides, expected) -> None:
    provider, closer = build_llm_provider(_settings(**overrides))
    assert isinstance(provider, expected)
    if expected is FakeStructuredLLMProvider:
        assert closer is None
    else:
        assert closer is not None
        await closer()


# --------------------------------------------------------------------- GigaChat


class GigaChatServer:
    """In-process fake of the GigaChat auth + chat endpoints."""

    def __init__(self, chat_responses: list[httpx.Response] | None = None, token_ttl_ms: int | None = None) -> None:
        self.auth_requests: list[httpx.Request] = []
        self.chat_requests: list[httpx.Request] = []
        self.chat_responses = chat_responses
        self.token_ttl_ms = token_ttl_ms
        self.issued = 0

    def chat_ok(self, content) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "model": "GigaChat-2-Max",
                "choices": [{"message": {"role": "assistant", "content": content}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 7},
            },
        )

    def handler(self, request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/oauth"):
            self.auth_requests.append(request)
            self.issued += 1
            body = {"access_token": f"{SECRET_TOKEN}-{self.issued}"}
            if self.token_ttl_ms is not None:
                body["expires_at"] = self.token_ttl_ms
            return httpx.Response(200, json=body)
        self.chat_requests.append(request)
        if self.chat_responses:
            return self.chat_responses.pop(0)
        return self.chat_ok(json.dumps(_soften_payload()))


class Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def _gigachat(server: GigaChatServer, clock: Clock | None = None) -> GigaChatStructuredLLMProvider:
    return GigaChatStructuredLLMProvider(
        credentials=SECRET_KEY,
        model="GigaChat-2-Max",
        client=httpx.AsyncClient(transport=httpx.MockTransport(server.handler)),
        clock=clock or Clock(),
    )


@pytest.mark.asyncio
async def test_gigachat_builds_strict_json_schema_request_and_validates_output() -> None:
    server = GigaChatServer()
    provider = _gigachat(server)

    response = await provider.generate(_request())

    SoftenResult.model_validate(response.payload)
    assert response.provider == "gigachat"
    assert response.model == "GigaChat-2-Max"
    assert (response.input_tokens, response.output_tokens) == (11, 7)

    auth = server.auth_requests[0]
    assert auth.headers["Authorization"] == f"Basic {SECRET_KEY}"
    assert auth.headers["RqUID"]
    assert auth.content == b"scope=GIGACHAT_API_PERS"

    chat = server.chat_requests[0]
    assert str(chat.url) == "https://api.giga.chat/v1/chat/completions"
    assert chat.headers["Authorization"] == f"Bearer {SECRET_TOKEN}-1"
    body = json.loads(chat.content)
    assert body["model"] == "GigaChat-2-Max"
    assert body["stream"] is False
    assert body["messages"][0] == {"role": "system", "content": "system rules"}
    assert json.loads(body["messages"][1]["content"]) == _request().user_payload
    fmt = body["response_format"]
    assert fmt["type"] == "json_schema"
    assert fmt["strict"] is True
    assert fmt["schema"] == SoftenResult.model_json_schema()
    assert fmt["schema"]["additionalProperties"] is False
    assert "rewritten_message" in fmt["schema"]["required"]


@pytest.mark.asyncio
async def test_gigachat_reuses_token_until_close_to_expiry() -> None:
    server = GigaChatServer()
    clock = Clock()
    provider = _gigachat(server, clock)

    await provider.generate(_request())
    clock.now += 25 * 60
    await provider.generate(_request())
    assert len(server.auth_requests) == 1

    clock.now += 4 * 60  # 29 minutes: inside the refresh margin
    await provider.generate(_request())
    assert len(server.auth_requests) == 2
    assert server.chat_requests[-1].headers["Authorization"] == f"Bearer {SECRET_TOKEN}-2"


@pytest.mark.asyncio
async def test_gigachat_refreshes_token_once_after_401() -> None:
    server = GigaChatServer()
    server.chat_responses = [httpx.Response(401), server.chat_ok(json.dumps(_soften_payload()))]
    provider = _gigachat(server)

    await provider.generate(_request())

    assert len(server.auth_requests) == 2
    assert len(server.chat_requests) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "chat_response",
    [
        httpx.Response(200, json={"choices": [{"message": {"content": "{not json"}}]}),
        httpx.Response(200, json={"choices": [{"message": {"content": "[1, 2]"}}]}),
        httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({"tone_applied": "x"})}}]}),
        httpx.Response(200, json={"choices": []}),
        httpx.Response(500, json={"message": "boom"}),
        httpx.Response(401),
    ],
    ids=["malformed-json", "non-object", "schema-invalid", "bad-shape", "http-500", "auth-401"],
)
async def test_gigachat_errors_do_not_leak_secrets_or_content(chat_response) -> None:
    server = GigaChatServer(chat_responses=[chat_response, chat_response])
    provider = _gigachat(server)

    with pytest.raises(Exception) as excinfo:
        await provider.generate(_request())

    text = str(excinfo.value)
    for secret in (SECRET_KEY, SECRET_TOKEN, PRIVATE_TEXT, "{not json"):
        assert secret not in text


@pytest.mark.asyncio
async def test_gigachat_auth_failure_and_network_error() -> None:
    def auth_fails(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "bad key"})

    provider = GigaChatStructuredLLMProvider(
        credentials=SECRET_KEY,
        model="GigaChat",
        client=httpx.AsyncClient(transport=httpx.MockTransport(auth_fails)),
    )
    with pytest.raises(RuntimeError, match="auth failed with HTTP 401") as excinfo:
        await provider.generate(_request())
    assert SECRET_KEY not in str(excinfo.value)

    def network_down(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("unreachable", request=request)

    provider = GigaChatStructuredLLMProvider(
        credentials=SECRET_KEY,
        model="GigaChat",
        client=httpx.AsyncClient(transport=httpx.MockTransport(network_down)),
    )
    with pytest.raises(RuntimeError, match="ConnectError"):
        await provider.generate(_request())


def test_gigachat_requires_credentials() -> None:
    with pytest.raises(ValueError, match="GIGACHAT_CREDENTIALS"):
        GigaChatStructuredLLMProvider(credentials="", model="GigaChat")


def test_gigachat_repr_hides_credentials() -> None:
    provider = _gigachat(GigaChatServer())
    assert SECRET_KEY not in repr(provider)


# --------------------------------------------------------------------- DeepSeek


class FakeResponses:
    def __init__(self, result=None, error: Exception | None = None) -> None:
        self.calls: list[dict] = []
        self.result = result
        self.error = error

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.result


def _deepseek(responses: FakeResponses) -> DeepSeekStructuredLLMProvider:
    return DeepSeekStructuredLLMProvider(
        api_key=SECRET_KEY,
        model="deepseek-chat",
        client=SimpleNamespace(responses=responses),
    )


def _deepseek_result(output_text) -> SimpleNamespace:
    return SimpleNamespace(
        output_text=output_text,
        model="deepseek-chat",
        usage=SimpleNamespace(input_tokens=13, output_tokens=5),
    )


@pytest.mark.asyncio
async def test_deepseek_builds_json_schema_text_format_and_validates_output() -> None:
    responses = FakeResponses(_deepseek_result(json.dumps(_soften_payload())))
    provider = _deepseek(responses)

    response = await provider.generate(_request())

    SoftenResult.model_validate(response.payload)
    assert response.provider == "deepseek"
    assert response.model == "deepseek-chat"
    assert (response.input_tokens, response.output_tokens) == (13, 5)

    call = responses.calls[0]
    assert call["model"] == "deepseek-chat"
    assert call["instructions"] == "system rules"
    assert json.loads(call["input"]) == _request().user_payload
    assert call["text"] == {
        "format": {
            "type": "json_schema",
            "name": "SoftenResult",
            "schema": SoftenResult.model_json_schema(),
        }
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "output_text",
    ["{not json", "[]", json.dumps({"tone_applied": "x"}), None],
    ids=["malformed-json", "non-object", "schema-invalid", "missing"],
)
async def test_deepseek_rejects_invalid_structured_output(output_text) -> None:
    provider = _deepseek(FakeResponses(_deepseek_result(output_text)))
    with pytest.raises(Exception) as excinfo:
        await provider.generate(_request())
    assert "{not json" not in str(excinfo.value)
    assert PRIVATE_TEXT not in str(excinfo.value)


class FakeApiError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"error with key {SECRET_KEY}")
        self.status_code = status_code


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (FakeApiError(401), "HTTP 401"),
        (FakeApiError(429), "HTTP 429"),
        (ConnectionError("down"), "ConnectionError"),
    ],
)
async def test_deepseek_api_errors_are_sanitized(error, expected) -> None:
    provider = _deepseek(FakeResponses(error=error))
    with pytest.raises(RuntimeError, match=expected) as excinfo:
        await provider.generate(_request())
    assert SECRET_KEY not in str(excinfo.value)


def test_deepseek_requires_api_key() -> None:
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        DeepSeekStructuredLLMProvider(api_key="", model="deepseek-chat", client=SimpleNamespace())


# ------------------------------------------------------------ cross-provider


@pytest.mark.asyncio
async def test_llm_generate_tool_revalidates_output_for_every_provider() -> None:
    gigachat = _gigachat(GigaChatServer())
    deepseek = _deepseek(FakeResponses(_deepseek_result(json.dumps(_soften_payload()))))

    for provider, name in ((gigachat, "gigachat"), (deepseek, "deepseek")):
        result = await LLMGenerateTool(provider).execute(
            system_instructions="system rules",
            user_payload={"message_request": {"text": PRIVATE_TEXT}},
            output_artifact="soften_result",
        )
        assert result.success, result.error
        assert isinstance(result.data, SoftenResult)
        assert result.metadata["provider"] == name

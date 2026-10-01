from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.miniapp import router as miniapp_router
from app.container import build_container
from app.main import MINIAPP_MOUNT_PATH, mount_miniapp_static
from app.settings import AppSettings


BOT_TOKEN = "123456:TEST_TOKEN"


def make_app(static_dir: Path, *, bot_token: str | None = BOT_TOKEN) -> tuple[FastAPI, bool]:
    settings = AppSettings(telegram_bot_token=bot_token)
    app = FastAPI()
    app.state.settings = settings
    app.state.container = build_container(settings)
    app.include_router(miniapp_router)
    mounted = mount_miniapp_static(app, static_dir)
    return app, mounted


def test_static_mount_serves_index_when_directory_exists(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<!doctype html><title>miniapp</title>", encoding="utf-8")
    app, mounted = make_app(tmp_path)

    assert mounted is True
    client = TestClient(app)
    response = client.get(f"{MINIAPP_MOUNT_PATH}/")
    assert response.status_code == 200
    assert "miniapp" in response.text


def test_static_mount_absent_when_directory_missing(tmp_path: Path) -> None:
    app, mounted = make_app(tmp_path / "missing")

    assert mounted is False
    client = TestClient(app)
    assert client.get(f"{MINIAPP_MOUNT_PATH}/").status_code == 404


def test_api_auth_unaffected_by_static_mount(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("ok", encoding="utf-8")
    app, _ = make_app(tmp_path)
    client = TestClient(app)

    response = client.post("/v1/miniapp/auth")
    assert response.status_code == 401


def test_api_auth_unconfigured_still_503_with_static_mount(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("ok", encoding="utf-8")
    app, _ = make_app(tmp_path, bot_token=None)
    client = TestClient(app)

    response = client.post("/v1/miniapp/auth")
    assert response.status_code == 503

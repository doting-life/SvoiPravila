from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.http import router as assist_router
from app.api.miniapp import router as miniapp_router
from app.api.telegram import router as telegram_router
from app.container import build_container
from app.settings import AppSettings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = AppSettings()
    container = build_container(settings)
    app.state.settings = settings
    app.state.container = container
    try:
        yield
    finally:
        await container.aclose()


app = FastAPI(title="Свои Правила API", version="0.3.0", lifespan=lifespan)
app.include_router(assist_router)
app.include_router(miniapp_router)
app.include_router(telegram_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.3.0"}

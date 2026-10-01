from __future__ import annotations

import asyncio

from app.persistence import build_async_engine, create_schema
from app.settings import AppSettings


async def main() -> None:
    settings = AppSettings()
    if not settings.database_url:
        raise SystemExit("DATABASE_URL is required")
    engine = build_async_engine(settings.database_url)
    try:
        await create_schema(engine)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

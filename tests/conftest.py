import importlib
from collections.abc import Iterator

import httpx
import pytest
from sqlmodel import Session


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def api_module(monkeypatch: pytest.MonkeyPatch, tmp_path: pytest.TempPathFactory):
    db_path = tmp_path / "test.sqlite"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("FEED_BASE_URL", "http://testserver/rss")

    import jarrl.api

    module = importlib.reload(jarrl.api)

    def fake_extract_article(url: str) -> dict:
        return {
            "title": "Example title",
            "description": "Example description",
            "published_at": None,
        }

    monkeypatch.setattr(module, "extract_article", fake_extract_article, raising=False)
    return module


@pytest.fixture
async def client(api_module) -> Iterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=api_module.app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
def session_factory(api_module):
    from jarrl.db import get_engine

    engine = get_engine()

    def factory() -> Session:
        return Session(engine)

    return factory

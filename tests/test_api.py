import pytest
from sqlmodel import select

from jarrl.models import Article


def test_app_imports():
    from jarrl.api import app

    assert app is not None


def test_main_module_exposes_app():
    from main import app

    assert app is not None


@pytest.mark.anyio
async def test_add_article_creates_row(client):
    response = await client.post("/add", json={"url": "https://example.com/article"})

    assert response.status_code == 201
    body = response.json()
    assert body["created"] is True
    assert body["article"]["url"] == "https://example.com/article"
    assert body["article"]["title"] == "Example title"


@pytest.mark.anyio
async def test_add_article_returns_existing_row_for_duplicates(client):
    first = await client.post("/add", json={"url": "https://example.com/article"})
    second = await client.post("/add", json={"url": "https://example.com/article"})

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["created"] is False
    assert second.json()["article"]["id"] == first.json()["article"]["id"]


@pytest.mark.anyio
async def test_add_article_rejects_invalid_url(client):
    response = await client.post("/add", json={"url": "not-a-url"})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_add_article_returns_400_for_parse_failure(client, monkeypatch):
    def fail_extract(url: str) -> dict:
        raise ValueError("parse failed")

    monkeypatch.setattr("jarrl.api.extract_article", fail_extract)

    response = await client.post("/add", json={"url": "https://example.com/article"})

    assert response.status_code == 400


@pytest.mark.anyio
async def test_parse_failure_does_not_store_row(client, session_factory, monkeypatch):
    def fail_extract(url: str) -> dict:
        raise ValueError("parse failed")

    monkeypatch.setattr("jarrl.api.extract_article", fail_extract)

    await client.post("/add", json={"url": "https://example.com/article"})

    with session_factory() as session:
        assert session.exec(select(Article)).all() == []


@pytest.mark.anyio
async def test_rss_endpoint_includes_saved_article(client):
    await client.post("/add", json={"url": "https://example.com/article"})

    response = await client.get("/rss")

    assert response.status_code == 200
    assert "application/rss+xml" in response.headers["content-type"]
    assert "Example title" in response.text
    assert "https://example.com/article" in response.text

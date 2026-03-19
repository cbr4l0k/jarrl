from datetime import UTC, datetime
from urllib.parse import urlparse

import httpx
from fastapi import Depends, FastAPI, Response
from fastapi.exceptions import HTTPException
from feedgen.feed import FeedGenerator
from sqlmodel import Session, select

from jarrl.config import get_feed_base_url
from jarrl.db import get_session, init_db
from jarrl.extractor import extract_article
from jarrl.models import AddArticleRequest, AddArticleResponse, Article, ArticlePayload


app = FastAPI()
init_db()


def _is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _feed_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@app.post("/add", response_model=AddArticleResponse, status_code=201)
async def add_article(
    payload: AddArticleRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> AddArticleResponse:
    if not _is_valid_url(payload.url):
        raise HTTPException(status_code=422, detail="URL must use http or https")

    existing_article = session.exec(
        select(Article).where(Article.url == payload.url)
    ).first()
    if existing_article is not None:
        response.status_code = 200
        return AddArticleResponse(
            created=False,
            article=ArticlePayload.model_validate(existing_article),
        )

    try:
        metadata = extract_article(payload.url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Failed to fetch article") from exc

    article = Article(
        url=payload.url,
        title=metadata.get("title"),
        description=metadata.get("description"),
        published_at=metadata.get("published_at"),
    )
    session.add(article)
    session.commit()
    session.refresh(article)
    response.status_code = 201
    return AddArticleResponse(created=True, article=ArticlePayload.model_validate(article))


@app.get("/rss")
async def rss(session: Session = Depends(get_session)) -> Response:
    feed = FeedGenerator()
    feed.title("JARRL")
    feed.link(href=get_feed_base_url(), rel="self")
    feed.description("Personal read-later feed")

    articles = session.exec(select(Article).order_by(Article.added_at.desc())).all()
    for article in articles:
        entry = feed.add_entry()
        entry.title(article.title or article.url)
        entry.link(href=article.url)
        entry.description(article.description or "")
        entry.pubDate(_feed_datetime(article.published_at or article.added_at))

    return Response(content=feed.rss_str(), media_type="application/rss+xml")

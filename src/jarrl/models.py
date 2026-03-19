from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Article(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    url: str = Field(index=True, unique=True)
    title: str | None = None
    description: str | None = None
    published_at: datetime | None = None
    added_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AddArticleRequest(SQLModel):
    url: str


class ArticlePayload(SQLModel):
    id: int
    url: str
    title: str | None
    description: str | None
    published_at: datetime | None
    added_at: datetime


class AddArticleResponse(SQLModel):
    created: bool
    article: ArticlePayload

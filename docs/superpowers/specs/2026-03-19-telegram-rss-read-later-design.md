# Telegram RSS Read-Later Bot Design

## Goal

Make the code in `src/main.py` work as a simple personal read-later system: send a URL to a Telegram bot, extract the article title and related metadata, store it, and expose the saved items as an RSS feed that a personal RSS reader can poll.

## Constraints

- Keep the implementation as simple as possible.
- Deploy with Docker and Docker Compose.
- Run locally/private-first rather than for public internet exposure.
- Prefer minimal moving parts; do not add a database server unless required.

## Current Problems

The existing `src/main.py` is not operational in its current form:

- It mixes the HTTP API and Telegram polling runtime in one file/process.
- It defines `MyArticle` but later uses `Article`, which is not the SQLModel table.
- It creates a SQLite engine with an invalid URL.
- It does not create tables or persist added articles.
- The Telegram bot posts to `localhost`, which will fail in a multi-container setup.
- It hardcodes the bot token in source.
- It lacks tests around persistence and RSS generation.

## Recommended Approach

Use two services in `docker-compose`:

- `api`: a FastAPI service that stores article records in SQLite and serves the RSS feed.
- `bot`: an aiogram polling worker that accepts Telegram messages and forwards valid URLs to the API.

Both services will share configuration through environment variables. SQLite storage will live on a named Docker volume mounted into the containers. Only the API needs direct database access.

This keeps the architecture aligned with the user intent while avoiding unnecessary infrastructure such as Postgres, Redis, queues, or a reverse proxy.

## Runtime Architecture

### API Service

Responsibilities:

- Create the SQLite schema on startup.
- Accept a submitted URL through `POST /add`.
- Extract article metadata from the URL.
- Insert a new article record if it does not already exist.
- Return the stored article and whether it was newly created or already present.
- Serve an RSS feed through `GET /rss`.

Configuration:

- `DATABASE_URL`: SQLAlchemy/SQLModel connection string, defaulting to a SQLite file under a mounted data directory.
- `FEED_BASE_URL`: base URL used when generating RSS self links, defaulting to a local/private address.

### Telegram Bot Service

Responsibilities:

- Poll Telegram using `BOT_TOKEN`.
- Accept text messages containing URLs.
- Reject empty or clearly invalid input with a short reply.
- Submit valid URLs to the API service using the compose service hostname.
- Reply differently for success, duplicate submissions, invalid input, and extraction failures.

Configuration:

- `BOT_TOKEN`: Telegram bot token.
- `API_BASE_URL`: base URL of the API service, defaulting to the compose hostname, for example `http://api:8000`.

Outcome mapping:

- API `201` with `"created": true` means the bot replies that the article was added.
- API `200` with `"created": false` means the bot replies that the URL was already saved.
- API `400`, `422`, or `502` means the bot replies that the URL could not be added and includes a short reason.
- Non-text Telegram messages are ignored or answered with a short prompt to send a URL.

## Data Model

Use a single `Article` SQLModel table with:

- `id`
- `url` (unique, indexed)
- `title`
- `description`
- `published_at` as an optional timezone-aware UTC datetime
- `added_at`

Keep the schema minimal. No tagging, read state, user accounts, or per-chat partitioning in this version.

## API Behavior

### `POST /add`

Input:

- JSON body:

```json
{"url": "https://example.com/article"}
```

Behavior:

- Validate that the URL is syntactically usable.
- Check whether the URL already exists in the database.
- If it exists, return HTTP `200` with the existing article and `"created": false`; do not create another row.
- If it does not exist:
  - extract metadata with `newspaper3k`
  - persist the record
  - return HTTP `201` with the stored article and `"created": true`

Success response shape:

```json
{
  "created": true,
  "article": {
    "id": 1,
    "url": "https://example.com/article",
    "title": "Example title",
    "description": "Example description",
    "published_at": "2026-03-19T12:34:56Z",
    "added_at": "2026-03-19T12:35:20Z"
  }
}
```

Failure handling:

- If the URL is missing or not an `http`/`https` URL, return HTTP `422`.
- If extraction fails because the page cannot be fetched or parsed into usable metadata, return HTTP `400` with a clear error message.
- If an upstream timeout or network problem prevents extraction, return HTTP `502` with a clear error message.
- Do not insert partial/broken rows when extraction fails.

### `GET /rss`

Behavior:

- Read all saved articles ordered by newest first.
- Build a valid RSS feed with one item per stored article.
- Use article title when available; otherwise fall back to the URL.
- Use extracted `published_at` when available; otherwise fall back to `added_at`.
- Serialize feed datetimes as timezone-aware UTC values.

## Containerization

### Dockerfile

Use one Python image and one project Dockerfile that can support both services. Compose will start different commands for `api` and `bot`.

The image should:

- install project dependencies
- copy source code
- expose the API port
- avoid embedding secrets

### docker-compose.yml

Define:

- `api` service
- `bot` service
- one named volume for SQLite data

Local usage should be as simple as:

```bash
docker compose up --build
```

## Project Layout Changes

Refactor away from one monolithic runtime file into small focused modules:

- application/config module for environment-backed settings
- database/model module for SQLModel engine and session handling
- extraction module for article metadata extraction
- API entry module
- bot entry module

The goal is not a large rewrite. The split is only to make each runtime independently executable and testable.

## Testing Requirements

Write tests before implementation changes for the API behavior:

- adding a new article stores one record
- adding the same URL twice does not create duplicates
- RSS endpoint includes stored article data
- extraction failures return an error without storing a row
- invalid URL input returns a validation error

Tests must stub the metadata extractor rather than making live network fetches.

Bot behavior may be lightly unit-tested if straightforward, but API tests are the priority because they cover the core workflow.

## Non-Goals

This version will not include:

- public deployment setup
- authentication
- multi-user support
- webhook delivery
- background job workers
- feed filtering, tagging, or read/unread states

## Success Criteria

The work is complete when:

- `docker compose up --build` starts both services successfully
- sending a valid URL to the Telegram bot causes it to be stored once
- `GET /rss` returns a usable RSS feed containing saved items
- the feed can be polled by a personal RSS reader on the local/private network
- configuration is driven by environment variables rather than hardcoded secrets
- automated tests cover the main API flow

# jarrl (forgot the meaning of the letters)

Send article URLs to a Telegram bot, store them once, and expose the saved items as an RSS feed for a private read-later queue.

## Local Setup

1. Copy `.env.example` to `.env` and set `BOT_TOKEN` to your Telegram bot token.
2. Set `ALLOWED_TELEGRAM_USER_ID` to your Telegram numeric user ID.
3. Start the stack:

```bash
docker compose up -d --build
```

The API runs on `http://localhost:8000` and the RSS feed is available at `http://localhost:8000/rss`.
The API runs on `http://localhost:8856` and the RSS feed is available at `http://localhost:8856/rss`.

Both services use Docker's `unless-stopped` restart policy. If Docker Desktop is set to launch when you log in, the stack will come back automatically after a reboot once you have started it at least once.

## Environment

- `BOT_TOKEN`: required for the bot container.
- `ALLOWED_TELEGRAM_USER_ID`: required numeric Telegram user ID allowed to use the bot.
- `API_BASE_URL`: API address used by the bot, defaults to `http://api:8000`.
- `DATABASE_URL`: SQLite URL, defaults to `sqlite:///./data/jarrl.sqlite`.
- `FEED_BASE_URL`: feed self-link, defaults to `http://localhost:8856/rss`.

## Behavior

- Send a valid `http` or `https` URL to the bot.
- The bot ignores messages from any Telegram user except `ALLOWED_TELEGRAM_USER_ID`.
- The API extracts the title and metadata, stores the article, and deduplicates by URL.
- Poll the RSS feed from your personal reader to keep a simple read-later list.

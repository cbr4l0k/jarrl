import asyncio
from urllib.parse import urlparse

import httpx
from aiogram import Bot, Dispatcher, types

from jarrl.config import (
    get_allowed_telegram_user_id,
    get_api_base_url,
    get_bot_token,
)


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def is_allowed_user(*, sender_user_id: int | None, allowed_user_id: int) -> bool:
    return sender_user_id is not None and sender_user_id == allowed_user_id


def format_add_result(*, created: bool, title: str | None, url: str | None = None) -> str:
    label = title or url or "Untitled"
    if created:
        return f"Added: {label}"
    return f"Already saved: {label}"


def format_error_response(detail: str) -> str:
    return f"Could not add URL: {detail}"


async def handle_url(message: types.Message) -> None:
    if not is_allowed_user(
        sender_user_id=message.from_user.id if message.from_user else None,
        allowed_user_id=get_allowed_telegram_user_id(),
    ):
        return

    text = (message.text or "").strip()
    if not text or not is_http_url(text):
        await message.reply("Send a valid http or https URL.")
        return

    async with httpx.AsyncClient(base_url=get_api_base_url()) as client:
        response = await client.post("/add", json={"url": text})

    if response.status_code in {200, 201}:
        payload = response.json()
        article = payload["article"]
        await message.reply(
            format_add_result(
                created=payload["created"],
                title=article["title"],
                url=article["url"],
            )
        )
        return

    detail = response.json().get("detail", "unknown error")
    await message.reply(format_error_response(detail))


async def main() -> None:
    bot = Bot(token=get_bot_token())
    dispatcher = Dispatcher()
    dispatcher.message.register(handle_url)

    max_retries = 60
    for attempt in range(max_retries):
        try:
            await dispatcher.start_polling(bot)
            return
        except Exception as exc:
            if attempt == max_retries - 1:
                raise
            delay = min(2 ** attempt, 30)
            print(
                f"Polling failed ({exc.__class__.__name__}), "
                f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})..."
            )
            await asyncio.sleep(delay)


if __name__ == "__main__":
    asyncio.run(main())

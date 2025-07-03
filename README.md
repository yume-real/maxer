# maxer – Async Python SDK for MAX Bot API

`maxer` is an asynchronous, typed wrapper around the [MAX.ru](https://max.ru) Bot & Mini-apps API. The goal is to provide an ergonomic developer experience similar to popular bot frameworks, while staying close to the official specification.

## Installation

```bash
pip install -r requirements.txt
```

*(The package will be published to PyPI later.)*

## Quick example

```python
import asyncio
from maxer import Client, models

TOKEN = "YOUR_BOT_TOKEN"

async def main():
    async with Client(TOKEN) as bot:
        me = await bot.get_me()
        print("Hello from", me.first_name)

        chats = await bot.get_chats()
        print("You have", len(chats), "chats")

        if chats:
            await bot.send_message(
                chat_id=chats[0].chat_id,
                body=models.NewMessageBody(text="Hello from async Python bot!"),
            )

asyncio.run(main())
```

## Features

* Async & await powered by `httpx`
* Typed Pydantic models generated from docs (work in progress)
* Automatic long-polling helper
* Full coverage of core endpoints (`/me`, `/chats`, `/messages`, `/updates`, ...)
* MIT licensed

## Roadmap

- [ ] Full coverage of media uploads & rich message builders
- [ ] High-level Dispatcher similar to aiogram
- [ ] Webhook server helpers (e.g. FastAPI integration)
- [ ] CLI tools for bot scaffolding 
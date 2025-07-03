from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bot import Bot


class CommandContext:
    def __init__(self, bot: "Bot", chat_id: int, message_id: str):
        self.bot = bot
        self.chat_id = chat_id
        self.message_id = message_id

    @property
    def chat(self):
        return self.bot.chat(self.chat_id)

    async def reply(self, text: str):
        await self.bot.client.messages.send(self.chat_id, text) 
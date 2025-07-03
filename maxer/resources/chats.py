from __future__ import annotations

from typing import Any, Dict, List, Sequence, TYPE_CHECKING

from ..core.enums import ChatAction
from ..core.models import Chat, Message

if TYPE_CHECKING:
    from ..core.client import MaxerClient


class ChatsAPI:
    def __init__(self, client: "MaxerClient"):
        self._c = client

    async def list(self, *, count: int | None = None, marker: int | None = None):
        return await self._c.get_chats(count=count, marker=marker)

    async def iter(self, *, batch_size: int = 100):
        async for ch in self._c.iter_chats(batch_size=batch_size):
            yield ch

    async def get(self, chat_id: int) -> Chat:
        return await self._c.get_chat(chat_id)

    async def get_by_link(self, link: str) -> Chat:
        return await self._c.get_chat_by_link(link)

    async def edit(self, chat_id: int, **fields) -> Chat:
        return await self._c.update_chat(chat_id, **fields)

    async def delete(self, chat_id: int) -> bool:
        return await self._c.delete_chat(chat_id)

    async def send_action(self, chat_id: int, action: ChatAction | str) -> bool:
        return await self._c.send_chat_action(chat_id, action)

    async def get_pin(self, chat_id: int) -> Message | None:
        return await self._c.get_pinned_message(chat_id)

    async def pin(self, chat_id: int, message_id: str) -> bool:
        return await self._c.pin_message(chat_id, message_id)

    async def unpin(self, chat_id: int) -> bool:
        return await self._c.unpin_message(chat_id)

    async def me(self, chat_id: int):
        return await self._c.get_chat_member_me(chat_id)

    async def leave(self, chat_id: int) -> bool:
        return await self._c.leave_chat(chat_id)

    async def admins(self, chat_id: int):
        return await self._c.get_chat_admins(chat_id)

    async def add_admin(self, chat_id: int, user_id: int) -> bool:
        return await self._c.add_chat_admin(chat_id, user_id)

    async def remove_admin(self, chat_id: int, user_id: int) -> bool:
        return await self._c.remove_chat_admin(chat_id, user_id)

    async def members(
        self,
        chat_id: int,
        *,
        user_ids: Sequence[int] | None = None,
        count: int | None = None,
        marker: int | None = None,
    ):
        return await self._c.get_chat_members(
            chat_id, user_ids=user_ids, count=count, marker=marker
        )

    async def add_members(self, chat_id: int, user_ids: Sequence[int]) -> bool:
        return await self._c.add_chat_members(chat_id, user_ids)

    async def remove_member(
        self,
        chat_id: int,
        user_id: int,
        *,
        block: bool | None = None,
    ) -> bool:
        return await self._c.remove_chat_member(chat_id, user_id, block=block)

    async def add_admins(self, chat_id: int, user_ids: Sequence[int]) -> bool:
        return await self._c.add_chat_admins(chat_id, user_ids) 
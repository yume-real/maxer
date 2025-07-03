from __future__ import annotations

from typing import Any, Dict, Union, TYPE_CHECKING
import os

from ..core.models import Message, NewMessageBody
from ..core.enums import ChatAction
from .message_builder import MessageBuilder

if TYPE_CHECKING:
    from ..core.client import MaxerClient


class ChatProxy:
    __slots__ = ("_c", "chat_id")

    def __init__(self, client: "MaxerClient", chat_id: int):
        self._c = client
        self.chat_id = chat_id

    async def send(
        self,
        body: Union[str, Dict[str, Any], NewMessageBody, None] = None,
        **body_kwargs,
    ) -> Message:
        return await self._c.messages.send(self.chat_id, body, **body_kwargs)

    async def edit(self, message_id: str, body: Union[str, Dict[str, Any], NewMessageBody, None] = None, **body_kwargs) -> Message:
        return await self._c.messages.edit(message_id, body, **body_kwargs)

    async def delete(self, message_id: str) -> bool:
        return await self._c.messages.delete(message_id=message_id)

    async def iter_messages(self, *, batch_size: int = 100):
        async for msg in self._c.iter_messages(chat_id=self.chat_id, batch_size=batch_size):
            yield msg

    async def list_messages(
        self,
        *,
        message_ids: list[str] | None = None,
        from_ts: int | None = None,
        to_ts: int | None = None,
        count: int | None = None,
    ):
        return await self._c.messages.list(
            chat_id=self.chat_id,
            message_ids=message_ids,
            from_ts=from_ts,
            to_ts=to_ts,
            count=count,
        )

    async def action(self, action: ChatAction | str):
        return await self._c.chats.send_action(self.chat_id, action)

    async def pin(self, message_id: str | None):
        if message_id is None:
            return await self._c.chats.unpin(self.chat_id)
        return await self._c.chats.pin(self.chat_id, message_id)

    async def unpin(self):
        return await self.pin(None)

    async def get_pin(self):
        return await self._c.chats.get_pin(self.chat_id)

    async def info(self):
        return await self._c.chats.get(self.chat_id)

    async def edit_info(self, **fields):
        return await self._c.chats.edit(self.chat_id, **fields)

    async def members_iter(self, *, batch_size: int = 100):
        marker: int | None = None
        while True:
            members, marker = await self._c.get_chat_members(self.chat_id, count=batch_size, marker=marker)
            for m in members:
                yield m
            if marker is None:
                break

    async def members(
        self,
        *,
        user_ids: list[int] | None = None,
        count: int | None = None,
    ):
        return await self._c.get_chat_members(self.chat_id, user_ids=user_ids, count=count)

    async def add_members(self, user_ids):
        return await self._c.add_chat_members(self.chat_id, user_ids)

    async def remove_member(self, user_id: int, *, block: bool | None = None):
        return await self._c.remove_chat_member(self.chat_id, user_id, block=block)

    async def send_photo(self, path: os.PathLike | str, *, text: str | None = None):
        info = await self._c.uploads.upload_image(path)
        file_id: str = str(info.get("file_id") or info.get("id"))
        att = {"type": "photo", "payload": {"file_id": file_id}}
        return await self.send(text, attachments=[att]) if text else await self.send(attachments=[att])

    async def send_audio(self, path: os.PathLike | str, *, text: str | None = None):
        info = await self._c.uploads.upload_audio(path)
        file_id: str = str(info.get("file_id") or info.get("id"))
        att = {"type": "audio", "payload": {"file_id": file_id}}
        return await self.send(text, attachments=[att]) if text else await self.send(attachments=[att])

    async def send_document(self, path: os.PathLike | str, *, text: str | None = None):
        info = await self._c.uploads.upload_document(path)
        file_id: str = str(info.get("file_id") or info.get("id"))
        att = {"type": "document", "payload": {"file_id": file_id}}
        return await self.send(text, attachments=[att]) if text else await self.send(attachments=[att])

    async def send_video(self, path: os.PathLike | str, *, text: str | None = None):
        info = await self._c.uploads.upload_video(path)
        file_id: str = str(info.get("token") or info.get("file_id"))
        att = {"type": "video", "payload": {"token": file_id}}
        return await self.send(text, attachments=[att]) if text else await self.send(attachments=[att])

    def message(self, text: str | None = None, **body_kwargs) -> MessageBuilder:
        payload: Dict[str, Any] = {}
        if text is not None:
            payload["text"] = text
        payload.update(body_kwargs)
        return MessageBuilder(self, payload) 
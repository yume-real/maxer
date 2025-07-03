from __future__ import annotations

from typing import Any, Dict, List, Tuple, TYPE_CHECKING

from ..core.models import Message, NewMessageBody

if TYPE_CHECKING:
    from ..core.client import MaxerClient


class MessagesAPI:

    def __init__(self, client: "MaxerClient"):
        self._c = client

    async def send(self, chat_id: int, body: NewMessageBody | str | Dict[str, Any] | None = None, **body_kwargs) -> Message:
        if isinstance(body, NewMessageBody):
            if body_kwargs:
                raise ValueError("body_kwargs are ignored when 'body' is already NewMessageBody")
            _body = body
        else:
            if isinstance(body, str):
                payload: Dict[str, Any] = {"text": body}
            elif isinstance(body, dict):
                payload = body.copy()
            elif body is None:
                payload = {}
            else:
                raise TypeError("body must be NewMessageBody | str | dict | None")

            if body_kwargs:
                payload.update(body_kwargs)

            _body = NewMessageBody(**payload)

        return await self._c.send_message(chat_id, _body)

    async def edit(
        self,
        message_id: str,
        body: NewMessageBody | str | Dict[str, Any] | None = None,
        **body_kwargs,
    ) -> Message:
        if isinstance(body, NewMessageBody):
            if body_kwargs:
                raise ValueError("body_kwargs are ignored when 'body' is already NewMessageBody")
            _body = body
        else:
            if isinstance(body, str):
                payload: Dict[str, Any] = {"text": body}
            elif isinstance(body, dict):
                payload = body.copy()
            elif body is None:
                payload = {}
            else:
                raise TypeError("body must be NewMessageBody | str | dict | None")

            if body_kwargs:
                payload.update(body_kwargs)

            _body = NewMessageBody(**payload)

        return await self._c.edit_message(message_id, _body)

    async def delete(self, *, message_id: str) -> bool:
        return await self._c.delete_message(message_id)

    async def get(self, message_id: str) -> Message:
        return await self._c.get_message(message_id)

    async def list(
        self,
        *,
        chat_id: int | None = None,
        message_ids: List[str] | None = None,
        from_ts: int | None = None,
        to_ts: int | None = None,
        count: int | None = None,
    ) -> Tuple[List[Message], int | None]:
        return await self._c.get_messages(
            chat_id=chat_id,
            message_ids=message_ids,
            from_ts=from_ts,
            to_ts=to_ts,
            count=count,
        )

    async def iter(self, *, chat_id: int, batch_size: int = 100):
        async for m in self._c.iter_messages(chat_id=chat_id, batch_size=batch_size):
            yield m

    async def video_info(self, token: str):
        return await self._c.get_video_info(token)

    async def answer_callback(
        self,
        callback_id: str,
        *,
        message: NewMessageBody | Dict[str, Any] | None = None,
        notification: str | None = None,
    ) -> bool:
        return await self._c.answer_callback(callback_id, message=message, notification=notification) 
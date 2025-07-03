from __future__ import annotations

from typing import Any, Dict, List, TYPE_CHECKING

from ..core.enums import TextFormat
from .button import Button

if TYPE_CHECKING:
    from .chat_proxy import ChatProxy
    from ..core.models import Message


class MessageBuilder:
    __slots__ = ("_chat", "_payload")

    def __init__(self, chat: "ChatProxy", payload: Dict[str, Any] | None = None):
        self._chat = chat
        self._payload: Dict[str, Any] = payload or {}

    def _clone(self, **updates) -> "MessageBuilder":
        new_payload = {**self._payload, **updates}
        return MessageBuilder(self._chat, new_payload)

    def text(self, value: str):
        return self._clone(text=value)

    def markdown(self):
        return self._clone(format=TextFormat.MARKDOWN)

    def html(self):
        return self._clone(format=TextFormat.HTML)

    def notify(self, value: bool):
        return self._clone(notify=value)

    def reply(self, message_id: str):
        return self._clone(reply_to=message_id)

    def buttons(self, buttons: List[Button] | List[Dict[str, Any]]):
        payload_list: List[Dict[str, Any]] = [b.to_dict() if isinstance(b, Button) else b for b in buttons]
        return self._clone(buttons=payload_list)

    def button(self, button: Button | str, *, callback: str | None = None, url: str | None = None):
        if isinstance(button, Button):
            btn_dict = button.to_dict()
        else:
            if callback is None and url is None:
                raise ValueError("Either callback or url must be provided for a button")
            btn_dict = {"text": button}
            if callback is not None:
                btn_dict["callback"] = callback
            if url is not None:
                btn_dict["url"] = url
        prev = self._payload.get("buttons") or []
        return self._clone(buttons=[*prev, btn_dict])

    def photo(self, file_id: str):
        prev = self._payload.get("attachments") or []
        photo_payload = {"type": "photo", "payload": {"file_id": file_id}}
        return self._clone(attachments=[*prev, photo_payload])

    def video(self, file_id: str):
        prev = self._payload.get("attachments") or []
        video_payload = {"type": "video", "payload": {"file_id": file_id}}
        return self._clone(attachments=[*prev, video_payload])

    def audio(self, file_id: str):
        prev = self._payload.get("attachments") or []
        audio_payload = {"type": "audio", "payload": {"file_id": file_id}}
        return self._clone(attachments=[*prev, audio_payload])

    def document(self, file_id: str):
        prev = self._payload.get("attachments") or []
        doc_payload = {"type": "document", "payload": {"file_id": file_id}}
        return self._clone(attachments=[*prev, doc_payload])

    async def send(self) -> "Message":
        return await self._chat.send(**self._payload) 
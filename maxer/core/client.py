from __future__ import annotations

import asyncio
import logging
import os
import pathlib
import time
from typing import Any, Dict, List, Optional, Sequence, AsyncGenerator

import httpx

from .exceptions import MaxerHTTPException, MaxerNetworkException
from .models import Chat, Message, NewMessageBody, Update, User, BotCommand
from .enums import ChatAction
from . import settings as _cfg

from ..utils.backoff import expo as _expo

_logger = logging.getLogger("maxer.core.client")


class MaxerClient:
    def __init__(
        self,
        token: str,
        *,
        base_url: str = _cfg.BASE_URL,
        timeout: float = _cfg.TIMEOUT,
        session: Optional[httpx.AsyncClient] = None,
    ):
        self.token = token
        self._close_session = session is None
        headers = {"User-Agent": _cfg.USER_AGENT_TEMPLATE.format(version=httpx.__version__)}
        self._client: httpx.AsyncClient = session or httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            params={"access_token": token},
            headers=headers,
        )

        from ..resources import (
            BotsAPI,
            ChatsAPI,
            MessagesAPI,
            SubscriptionsAPI,
            UploadsAPI,
        )

        self.bots = BotsAPI(self)
        self.chats = ChatsAPI(self)
        self.messages = MessagesAPI(self)
        self.subscriptions = SubscriptionsAPI(self)
        self.uploads = UploadsAPI(self)

    async def request(self, method: str, url: str, **kwargs) -> Any:
        _logger.debug("%s %s %s", method, url, kwargs.get("params") or kwargs.get("json") or "")
        attempt = 0
        while True:
            try:
                resp = await self._client.request(method, url, **kwargs)
            except httpx.RequestError as exc:
                attempt += 1
                if attempt >= _cfg.RETRY_ATTEMPTS:
                    raise MaxerNetworkException(str(exc)) from exc
                delay = await _expo(attempt - 1, base=_cfg.RETRY_BACKOFF_BASE)
                _logger.warning("Network error %s – retrying in %.1fs", exc, delay)
                await asyncio.sleep(delay)
                continue

            if resp.status_code >= 500:
                attempt += 1
                if attempt >= _cfg.RETRY_ATTEMPTS:
                    raise MaxerHTTPException(resp.status_code, resp.text)
                delay = await _expo(attempt - 1, base=_cfg.RETRY_BACKOFF_BASE)
                _logger.warning("Server error %s – retrying in %.1fs", resp.status_code, delay)
                await asyncio.sleep(delay)
                continue
            break

        _logger.debug("Response %s %s", resp.status_code, resp.text[:200])
        if resp.status_code >= 400:
            if resp.headers.get("content-type", "").startswith("application/json"):
                data = resp.json()
                if isinstance(data, dict) and "error" in data:
                    from .exceptions import MaxerAPIError

                    raise MaxerAPIError(resp.status_code, data["error"])
            raise MaxerHTTPException(resp.status_code, resp.text)

        if resp.headers.get("content-type", "").startswith("application/json"):
            return resp.json()
        return resp.text

    async def get_me(self) -> User:
        data = await self.request("GET", "/me")
        return User.parse_obj(data)

    async def update_me(
        self,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        description: str | None = None,
        commands: list["BotCommand"] | None = None,
        photo: dict[str, Any] | None = None,
    ) -> User:
        payload: Dict[str, Any] = {}
        if first_name is not None:
            payload["first_name"] = first_name
        if last_name is not None:
            payload["last_name"] = last_name
        if description is not None:
            payload["description"] = description
        if commands is not None:
            payload["commands"] = [c.dict(by_alias=True) if isinstance(c, BotCommand) else c for c in commands]
        if photo is not None:
            payload["photo"] = photo
        data = await self.request("PATCH", "/me", json=payload)
        return User.parse_obj(data)

    async def get_chats(self, *, count: int | None = None, marker: int | None = None) -> tuple[list[Chat], int | None]:
        params: Dict[str, Any] = {}
        if count is not None:
            params["count"] = count
        if marker is not None:
            params["marker"] = marker
        data = await self.request("GET", "/chats", params=params)
        return [Chat.parse_obj(c) for c in data["chats"]], data.get("marker")

    async def get_chat(self, chat_id: int) -> Chat:
        data = await self.request("GET", f"/chats/{chat_id}")
        return Chat.parse_obj(data)

    async def get_chat_by_link(self, chat_link: str) -> Chat:
        try:
            data = await self.request("GET", f"/chats/{chat_link}")
        except MaxerHTTPException as exc:
            if exc.status_code == 404:
                data = await self.request("GET", f"/chats/link/{chat_link}")
            else:
                raise
        return Chat.parse_obj(data)

    async def update_chat(self, chat_id: int, **fields) -> Chat:
        data = await self.request("PATCH", f"/chats/{chat_id}", json=fields)
        return Chat.parse_obj(data)

    async def delete_chat(self, chat_id: int) -> bool:
        await self.request("DELETE", f"/chats/{chat_id}")
        return True

    async def iter_chats(self, *, batch_size: int = 100):
        marker: int | None = None
        while True:
            chats, marker = await self.get_chats(count=batch_size, marker=marker)
            for ch in chats:
                yield ch
            if marker is None:
                break

    async def send_message(self, chat_id: int, body: NewMessageBody) -> Message:
        payload = body.dict(exclude_none=True)
        data = await self.request("POST", "/messages", json={"chat_id": chat_id, **payload})
        return Message.parse_obj(data)

    async def edit_message(self, message_id: str, body: NewMessageBody) -> Message:
        payload = body.dict(exclude_none=True)
        data = await self.request("PUT", "/messages", json={"message_id": message_id, **payload})
        return Message.parse_obj(data)

    async def delete_message(self, message_id: str) -> bool:
        await self.request("DELETE", "/messages", params={"message_id": message_id})
        return True

    async def iter_messages(self, *, chat_id: int, batch_size: int = 100):
        marker: int | None = None
        while True:
            msgs, marker = await self.get_messages(chat_id=chat_id, count=batch_size, marker=marker)
            for m in msgs:
                yield m
            if marker is None:
                break

    async def get_messages(
        self,
        *,
        chat_id: int | None = None,
        message_ids: list[str] | None = None,
        from_ts: int | None = None,
        to_ts: int | None = None,
        marker: int | None = None,
        count: int | None = None,
    ) -> tuple[list[Message], int | None]:
        params: Dict[str, Any] = {}
        if chat_id is not None:
            params["chat_id"] = chat_id
        if message_ids:
            params["message_ids"] = ",".join(message_ids)
        if from_ts is not None:
            params["from"] = from_ts
        if to_ts is not None:
            params["to"] = to_ts
        if marker is not None:
            params["marker"] = marker
        if count is not None:
            params["count"] = count
        data = await self.request("GET", "/messages", params=params)
        return [Message.parse_obj(m) for m in data["messages"]], data.get("marker")

    async def get_message(self, message_id: str) -> Message:
        data = await self.request("GET", f"/messages/{message_id}")
        return Message.parse_obj(data)

    async def get_video_info(self, video_token: str) -> Dict[str, Any]:
        return await self.request("GET", f"/videos/{video_token}")

    async def answer_callback(
        self,
        callback_id: str,
        *,
        message: "NewMessageBody" | Dict[str, Any] | None = None,
        notification: str | None = None,
    ) -> bool:
        payload: Dict[str, Any] = {"callback_id": callback_id}
        if message is not None:
            payload["message"] = (
                message.dict(by_alias=True) if isinstance(message, NewMessageBody) else message
            )
        if notification is not None:
            payload["notification"] = notification
        data = await self.request("POST", "/answers", json=payload)
        return bool(data.get("success", False))

    async def get_subscriptions(self) -> list[dict[str, Any]]:
        return await self.request("GET", "/subscriptions")

    async def subscribe(self, url: str, types: Sequence[str]) -> bool:
        await self.request("POST", "/subscriptions", json={"url": url, "types": list(types)})
        return True

    async def unsubscribe(self) -> bool:
        await self.request("DELETE", "/subscriptions")
        return True

    async def get_upload_url(self, file_type: str) -> str:
        data = await self.request("POST", "/uploads", json={"type": file_type})
        return data["upload_url"]

    async def upload_file(self, file_path: os.PathLike | str, file_type: str) -> Dict[str, Any]:
        path = pathlib.Path(file_path)
        url = await self.get_upload_url(file_type)
        _logger.debug("Uploading %s to %s", path, url)
        async with httpx.AsyncClient(timeout=_cfg.TIMEOUT) as up:
            with path.open("rb") as fp:
                resp = await up.post(url, files={"data": (path.name, fp)})
                resp.raise_for_status()
                return resp.json()

    async def upload_video(self, path: os.PathLike | str) -> Dict[str, Any]:
        return await self.upload_file(path, "video")

    async def get_updates(self, offset: str | None = None, limit: int = 100, timeout: int = 30) -> List[Update]:
        params: Dict[str, Any] = {"limit": limit, "timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        data = await self.request("GET", "/updates", params=params)
        return [Update.parse_obj(item) for item in data]

    async def long_poll(self, handler, *, poll_interval: float = 0.5):
        offset: str | None = None
        while True:
            updates = await self.get_updates(offset=offset)
            if updates:
                offset = updates[-1].update_id
                for upd in updates:
                    await handler(upd)
            await asyncio.sleep(poll_interval)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._close_session:
            await self._client.aclose()

    async def send_chat_action(self, chat_id: int, action: ChatAction | str) -> bool:
        await self.request("POST", f"/chats/{chat_id}/actions", json={"action": str(action)})
        return True

    async def get_pinned_message(self, chat_id: int) -> Message | None:
        data = await self.request("GET", f"/chats/{chat_id}/pin")
        if not data:
            return None
        return Message.parse_obj(data)

    async def pin_message(self, chat_id: int, message_id: str) -> bool:
        await self.request("PUT", f"/chats/{chat_id}/pin", json={"message_id": message_id})
        return True

    async def unpin_message(self, chat_id: int) -> bool:
        await self.request("DELETE", f"/chats/{chat_id}/pin")
        return True

    async def get_chat_member_me(self, chat_id: int):
        return await self.request("GET", f"/chats/{chat_id}/members/me")

    async def leave_chat(self, chat_id: int) -> bool:
        await self.request("DELETE", f"/chats/{chat_id}/members/me")
        return True

    async def get_chat_admins(self, chat_id: int):
        return await self.request("GET", f"/chats/{chat_id}/members/admins")

    async def add_chat_admin(self, chat_id: int, user_id: int) -> bool:
        await self.request("POST", f"/chats/{chat_id}/members/admins", json={"user_id": user_id})
        return True

    async def remove_chat_admin(self, chat_id: int, user_id: int) -> bool:
        await self.request("DELETE", f"/chats/{chat_id}/members/admins/{user_id}")
        return True

    async def get_chat_members(
        self,
        chat_id: int,
        *,
        user_ids: Sequence[int] | None = None,
        count: int | None = None,
        marker: int | None = None,
    ) -> tuple[list[dict[str, Any]], int | None]:
        params: Dict[str, Any] = {}
        if user_ids:
            params["user_ids"] = ",".join(map(str, user_ids))
        if count is not None:
            params["count"] = count
        if marker is not None:
            params["marker"] = marker
        data = await self.request("GET", f"/chats/{chat_id}/members", params=params)
        return data.get("members", []), data.get("marker")

    async def add_chat_members(self, chat_id: int, user_ids: Sequence[int]) -> bool:
        await self.request("POST", f"/chats/{chat_id}/members", json={"user_ids": list(user_ids)})
        return True

    async def remove_chat_member(
        self,
        chat_id: int,
        user_id: int,
        *,
        block: bool | None = None,
    ) -> bool:
        params: Dict[str, Any] = {"user_id": user_id}
        if block is not None:
            params["block"] = str(block).lower()
        await self.request("DELETE", f"/chats/{chat_id}/members", params=params)
        return True

    async def add_chat_admins(self, chat_id: int, user_ids: Sequence[int]) -> bool:
        payload = {"admins": [{"user_id": uid} for uid in user_ids]}
        await self.request("POST", f"/chats/{chat_id}/members/admins", json=payload)
        return True 
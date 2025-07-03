from __future__ import annotations

from typing import List, Optional, Dict, Any, Union

from pydantic import BaseModel, Field, model_validator

from .enums import ChatType, ChatStatus, MessageType, TextFormat


class BotCommand(BaseModel):
    command: str = Field(..., alias="command")
    description: str | None = None


class User(BaseModel):
    user_id: int = Field(..., alias="user_id")
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    is_bot: bool
    avatar_url: Optional[str] = None
    full_avatar_url: Optional[str] = None
    commands: Optional[List[BotCommand]] = None


class Attachment(BaseModel):
    type: str
    payload: Dict[str, Any]


class NewMessageLink(BaseModel):
    url: str | None = None
    text: str | None = None


class Recipient(BaseModel):
    user_id: int | None = Field(None, alias="user_id")
    chat_id: int | None = Field(None, alias="chat_id")

    @model_validator(mode="before")
    def _ensure_one_id(cls, values):
        if values.get("user_id") is None and values.get("chat_id") is None:
            raise ValueError("Recipient must contain either user_id or chat_id")
        return values


class MessageStat(BaseModel):
    views: int | None = None
    forwards: int | None = None
    reactions: Dict[str, int] | None = None

    class Config:
        extra = "allow"


class Message(BaseModel):
    message_id: str = Field(..., alias="message_id")
    chat_id: int | None = None

    sender: User | None = None
    recipient: Recipient | None = None

    type: MessageType

    timestamp: int | None = Field(None, alias="timestamp")
    date: int | None = Field(None, alias="date")
    link: Dict[str, Any] | None = None
    body: Dict[str, Any] | None = None
    stat: MessageStat | None = None
    url: str | None = None

    from_id: int | None = Field(None, alias="from_id")

    @model_validator(mode="before")
    def _migrate_legacy_fields(cls, values):
        if values.get("sender") is None and values.get("from_id") is not None:
            values["sender"] = {"user_id": values["from_id"]}
        if values.get("timestamp") is None and values.get("date") is not None:
            values["timestamp"] = values["date"]
        return values


class NewMessageBody(BaseModel):
    text: Optional[str] = None
    attachments: Optional[List[Attachment]] = None
    link: Optional[NewMessageLink] = None
    notify: bool | None = True
    format: TextFormat | None = None
    reply_to: Optional[str] = None
    buttons: Optional[List[Dict[str, Any]]] = None

    @model_validator(mode="after")
    def _ensure_content(cls, values):  # noqa: N805
        if not any(values.get(k) for k in ("text", "attachments", "link")):
            raise ValueError("NewMessageBody must contain at least text, attachments or link")
        return values


class Chat(BaseModel):
    chat_id: int = Field(..., alias="chat_id")
    type: ChatType
    status: ChatStatus
    title: Optional[str] = None
    last_event_time: int | None = None
    participants_count: int | None = None
    is_public: bool | None = None
    link: Optional[str] = None
    description: Optional[str] = None


class Update(BaseModel):
    update_id: str = Field(..., alias="update_id")
    type: str
    data: Dict[str, Any] 
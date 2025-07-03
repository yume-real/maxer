from enum import Enum


class ChatType(str, Enum):
    CHAT = "chat"

    DIALOG = CHAT


class ChatStatus(str, Enum):
    ACTIVE = "active"
    REMOVED = "removed"
    LEFT = "left"
    CLOSED = "closed"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    FILE = "file"
    AUDIO = "audio"
    STICKER = "sticker"


class ChatAction(str, Enum):
    TYPING_ON = "typing_on"
    SENDING_PHOTO = "sending_photo"
    SENDING_VIDEO = "sending_video"
    SENDING_AUDIO = "sending_audio"
    SENDING_FILE = "sending_file"
    MARK_SEEN = "mark_seen"

    TYPING = TYPING_ON
    UPLOAD_PHOTO = SENDING_PHOTO  
    RECORD_VIDEO = SENDING_VIDEO  
    UPLOAD_VIDEO = SENDING_VIDEO  
    RECORD_VOICE = SENDING_AUDIO  
    UPLOAD_VOICE = SENDING_AUDIO 


class TextFormat(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html" 
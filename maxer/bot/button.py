from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any

__all__ = ["Button"]


@dataclass(frozen=True, slots=True)
class Button:
    text: str
    callback: Optional[str] = None
    url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"text": self.text}
        if self.callback is not None:
            d["callback"] = self.callback
        if self.url is not None:
            d["url"] = self.url
        return d 
from __future__ import annotations

from typing import Any, List, Dict, TYPE_CHECKING

from ..core.models import User, BotCommand

if TYPE_CHECKING:
    from ..core.client import MaxerClient


class BotsAPI:
    def __init__(self, client: "MaxerClient"):
        self._c = client

    async def get_me(self) -> User:
        return await self._c.get_me()

    async def update_me(
        self,
        *,
        first_name: str | None = None,
        last_name: str | None = None,
        description: str | None = None,
        commands: List[BotCommand] | None = None,
        photo: Dict[str, Any] | None = None,
    ) -> User:
        return await self._c.update_me(
            first_name=first_name,
            last_name=last_name,
            description=description,
            commands=commands,
            photo=photo,
        ) 
from typing import Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.client import MaxerClient


class SubscriptionsAPI:
    def __init__(self, client: "MaxerClient"):
        self._c = client

    async def list(self):
        return await self._c.get_subscriptions()

    async def subscribe(self, url: str, types: Sequence[str]) -> bool:
        return await self._c.subscribe(url, types)

    async def unsubscribe(self) -> bool:
        return await self._c.unsubscribe() 
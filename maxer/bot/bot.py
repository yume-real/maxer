from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, List, TYPE_CHECKING, Optional, Pattern
import re
import typing as _t
from types import SimpleNamespace
from typing import cast

from ..core.client import MaxerClient
from ..core.models import Update
from .context import CommandContext
from .chat_proxy import ChatProxy

if TYPE_CHECKING:
    from ..core.models import NewMessageBody

_logger = logging.getLogger("maxer.bot")

EventHandler = Callable[..., Awaitable[None]]
CommandHandler = Callable[[CommandContext, str], Awaitable[None]]


class Bot:
    PREFIX = "/"

    def __init__(self, token: str, **client_kwargs):
        self.client = MaxerClient(token, **client_kwargs)
        self._event_handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._commands: Dict[str, CommandHandler] = {}
        self._message_handlers: List[CommandHandler] = []
        from typing import Any as _Any
        self._middlewares: List[_Any] = []

    def event(self, coro: EventHandler):
        name = coro.__name__
        if not name.startswith("on_"):
            raise ValueError("Event handler must be named on_<event>")
        self._event_handlers[name].append(coro)
        return coro

    async def _dispatch(self, name: str, *args):
        for handler in self._event_handlers.get(name, []):
            await handler(*args)

    def command(self, name: str | Callable[..., Any] | None = None):
        if callable(name) and inspect.iscoroutinefunction(name):
            func = _t.cast(Callable[..., Any], name)
            cmd_name = func.__name__
            self._register_command(cmd_name, func)
            return func

        def decorator(func: CommandHandler):
            cmd_name = name if isinstance(name, str) and name else func.__name__
            self._register_command(cmd_name, func)
            return func

        return decorator

    def _register_command(self, cmd_name: str, func: CommandHandler):
        if not inspect.iscoroutinefunction(func):
            raise TypeError("Command handler must be async def")
        self._commands[cmd_name] = func

    async def _handle_new_message(self, upd: Update):
        chat_id: int | None = upd.data.get("chat_id")
        text: str | None = upd.data.get("text")
        if chat_id is None or text is None:
            return

        message_id = upd.data.get("message_id")
        if message_id is None:
            return

        ctx = CommandContext(self, chat_id, message_id)
        if text.startswith(self.PREFIX):
            parts = text.lstrip(self.PREFIX).split()
            if parts:
                cmd_name, *args = parts
                cmd = self._commands.get(cmd_name)
                if cmd is not None:
                    await cmd(ctx, *args)
                    return

        for handler in self._message_handlers:
            await handler(ctx, text)

    def on(self, event_name: str):
        def decorator(func: EventHandler):
            if not inspect.iscoroutinefunction(func):
                raise TypeError("Event handler must be async def")
            self._event_handlers[f"on_{event_name}"].append(func)
            return func

        return decorator

    def message(self, pattern: str | Pattern[str] | Callable[[str], bool] | None = None):
        regex: Optional[Pattern[str]] = None
        predicate: Optional[Callable[[str], bool]] = None

        if pattern is not None and callable(pattern) and inspect.iscoroutinefunction(pattern):
            func = pattern
            pattern = None
            decorator = cast(Any, self.message(None))
            return decorator(cast(CommandHandler, func))

        if isinstance(pattern, (str, re.Pattern)):
            regex = re.compile(pattern) if isinstance(pattern, str) else pattern
        elif callable(pattern):
            predicate = pattern
        elif pattern is not None:
            raise TypeError("pattern must be str | Pattern | predicate | None | coroutine function")

        def decorator(func: CommandHandler):
            if not inspect.iscoroutinefunction(func):
                raise TypeError("Message handler must be async def")

            async def _wrapped(ctx: CommandContext, text: str):
                if regex is not None and not regex.search(text):
                    return
                if predicate is not None and not predicate(text):
                    return
                await func(ctx, text)

            self._message_handlers.append(_wrapped)
            return func

        return decorator

    def use(self, mw):
        if not callable(mw):
            raise TypeError("Middleware must be callable")
        self._middlewares.append(mw)

    async def _run_middlewares(self, upd: Update):
        async def terminal(update: Update):
            await self._route_update(update)

        next_callable = terminal
        for mw in reversed(self._middlewares):
            curr_mw = mw

            async def make_next(nxt, current):
                async def _wrapper(update: Update):
                    await current(update, nxt)
                return _wrapper

            next_callable = await make_next(next_callable, curr_mw)

        await next_callable(upd)

    async def _route_update(self, upd: Update):
        if upd.type == "new_message":
            await self._handle_new_message(upd)

        await self._dispatch("on_update", upd)
        await self._dispatch(f"on_{upd.type}", upd)

    async def start(self):
        await self._dispatch("on_ready")
        await self.client.long_poll(self._update_router)

    def run(self):
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            _logger.info("Bot stopped by user")

    def chat(self, chat_id: int) -> ChatProxy:
        return ChatProxy(self.client, chat_id)

    async def _update_router(self, upd: Update):
        if self._middlewares:
            await self._run_middlewares(upd)
        else:
            await self._route_update(upd) 
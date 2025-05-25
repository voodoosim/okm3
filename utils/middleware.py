import asyncio
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit: float = 0.5):
        self.limit = limit
        self.last_call: Dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if user_id:
            current_time = asyncio.get_event_loop().time()
            last_call_time = self.last_call.get(user_id, 0)
            if current_time - last_call_time < self.limit:
                await event.answer("너무 빠르게 요청하고 있습니다. 잠시 기다려 주세요.")
                return None
            self.last_call[user_id] = current_time
        return await handler(event, data)

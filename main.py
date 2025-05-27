import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, LOG_CHANNEL_ID, PUBLIC_LOG_CHANNEL_ID, logger
from database.setup import init_db
from handlers import admin, ban, bot_events, group, kick, mute, unban
from utils.logger import test_channel_access
from utils.middleware import ThrottlingMiddleware


async def main():
    logging.basicConfig(level=logging.INFO)
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # 데이터베이스 초기화
    await init_db()

    # 채널 접근 테스트
    await test_channel_access(bot, LOG_CHANNEL_ID)
    await test_channel_access(bot, PUBLIC_LOG_CHANNEL_ID)

    # 미들웨어 및 핸들러 등록
    dp.message.middleware(ThrottlingMiddleware(limit=1.0))
    dp.include_router(admin.router)
    dp.include_router(ban.router)
    dp.include_router(kick.router)
    dp.include_router(unban.router)
    dp.include_router(group.router)
    dp.include_router(bot_events.router)
    dp.include_router(mute.router)

    # 폴링 시작
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error("polling_error", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())

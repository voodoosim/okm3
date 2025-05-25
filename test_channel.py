import asyncio
import logging

from aiogram import Bot

from config import BOT_TOKEN, LOG_CHANNEL_ID, PUBLIC_LOG_CHANNEL_ID

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_channel():
    bot = Bot(token=BOT_TOKEN)  # BOT_TOKEN은 str로 보장됨
    try:
        for channel_id in [LOG_CHANNEL_ID, PUBLIC_LOG_CHANNEL_ID]:
            try:
                await bot.send_message(channel_id, "Test")
                logger.info(f"Test message sent to {channel_id}")
            except Exception as e:
                logger.error(f"Failed to send to {channel_id}: {str(e)}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(test_channel())

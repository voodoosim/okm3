from aiogram import Bot
from aiogram.types import ChatMember, ChatMemberOwner, ChatMemberAdministrator
from config import MASTER_ADMIN_IDS, logger

async def is_admin(user_id: int) -> bool:
    """사용자가 마스터 관리자인지 확인."""
    try:
        result = user_id in MASTER_ADMIN_IDS
        logger.info("is_admin_check", user_id=user_id, result=result)
        return result
    except Exception as e:
        logger.error("is_admin_error", user_id=user_id, error=str(e))
        return False

async def is_group_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    """사용자가 그룹 관리자인지 확인."""
    try:
        chat_member = await bot.get_chat_member(chat_id, user_id)
        result = isinstance(chat_member, (ChatMemberOwner, ChatMemberAdministrator))
        logger.info(
            "is_group_admin_check",
            user_id=user_id,
            chat_id=chat_id,
            result=result,
            member_status=chat_member.status
        )
        return result
    except Exception as e:
        logger.error("is_group_admin_error", user_id=user_id, chat_id=chat_id, error=str(e))
        return False

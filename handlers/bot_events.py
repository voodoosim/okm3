from aiogram import Bot, Router, types  # types 임포트 추가
from aiogram.filters import JOIN_TRANSITION, ChatMemberUpdatedFilter
from aiogram.types import ChatMemberUpdated

from config import LOG_CHANNEL_ID, MASTER_ADMIN_IDS, logger
from utils.logger import log_bot_added

router = Router()


@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def on_bot_added(event: ChatMemberUpdated, bot: Bot):
    """봇이 그룹에 추가되었을 때 처리."""
    chat = event.chat
    inviter = event.from_user
    chat_id = chat.id
    chat_title = chat.title or "Unknown"
    inviter_id = inviter.id
    inviter_username = inviter.username or "Unknown"

    # 봇의 관리자 권한 확인
    try:
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        is_admin = isinstance(
            bot_member, (types.ChatMemberAdministrator, types.ChatMemberOwner)
        )
    except Exception as e:
        logger.error("check_bot_admin_failed", chat_id=chat_id, error=str(e))
        is_admin = False

    # 그룹 링크 가져오기
    chat_link = None
    try:
        if chat.username:
            chat_link = f"https://t.me/{chat.username}"
        else:
            chat_invite = await bot.create_chat_invite_link(chat_id, member_limit=1)
            chat_link = chat_invite.invite_link
    except Exception as e:
        logger.warning("get_chat_link_failed", chat_id=chat_id, error=str(e))

    # 관리자 로그 채널에 기록
    await log_bot_added(
        bot, chat_title, chat_id, inviter_id, inviter_username, is_admin, chat_link
    )

    # 무단 설치 시 마스터 관리자에게 알림 전송
    if is_admin and inviter_id not in MASTER_ADMIN_IDS:
        for admin_id in MASTER_ADMIN_IDS:
            try:
                warning_message = (
                    f"⚠️ 봇이 무단으로 설치됨:\n"
                    f"그룹: [{chat_title} ({chat_id})]\n"
                    f"초대자: @{inviter_username} ({inviter_id})\n"
                    f"링크: {chat_link or '비공개 그룹'}"
                )
                await bot.send_message(admin_id, warning_message)
                logger.info(
                    "unauthorized_install_notification_sent",
                    admin_id=admin_id,
                    chat_id=chat_id,
                )
            except Exception as e:
                logger.error(
                    "send_unauthorized_notification_failed",
                    admin_id=admin_id,
                    chat_id=chat_id,
                    error=str(e),
                )

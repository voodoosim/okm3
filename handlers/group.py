from aiogram import Bot, Router, types
from aiogram.filters import Command

from config import logger
from database.groups import add_group, get_groups, remove_group
from utils.logger import log_group_add, log_group_remove
from utils.permissions import is_admin, is_group_admin

router = Router()


@router.message(Command(commands=["reload", "재장전"], prefix="."))
async def reload_group(message: types.Message, bot: Bot) -> None:
    """그룹 재장전 명령어 (.재장전)."""
    logger.info(
        "reload_group_triggered",
        user_id=message.from_user.id if message.from_user else None,
        chat_id=message.chat.id,
        text=message.text,
    )

    if not message.from_user:
        logger.error("reload_group_error", error="No user information")
        await message.reply("사용자 정보를 확인할 수 없습니다.")
        return

    is_admin_result = await is_admin(message.from_user.id)
    is_group_admin_result = await is_group_admin(
        bot, message.chat.id, message.from_user.id
    )
    logger.info(
        "permission_check",
        user_id=message.from_user.id,
        is_admin=is_admin_result,
        is_group_admin=is_group_admin_result,
    )

    if not (is_admin_result or is_group_admin_result):
        logger.warning(
            "permission_denied", user_id=message.from_user.id, chat_id=message.chat.id
        )
        await message.reply("권한이 없습니다.")
        return

    if message.chat.type == "private":
        logger.warning(
            "private_chat", user_id=message.from_user.id, chat_id=message.chat.id
        )
        await message.reply("그룹에서만 사용 가능합니다.")
        return

    chat_title = message.chat.title or "Unknown"
    try:
        success = await add_group(message.chat.id, chat_title, message.from_user.id)
        if success:
            await log_group_add(
                bot,
                chat_title,
                message.chat.id,
                message.from_user.id,
                message.from_user.username or "Unknown",
            )
            logger.info(
                "reload_group_success", chat_id=message.chat.id, chat_title=chat_title
            )
            await message.reply(f"그룹 '{chat_title}' 재장전 완료")
            logger.info(
                "reply_sent", chat_id=message.chat.id, message="그룹 재장전 완료"
            )
        else:
            logger.error(
                "add_group_failed", chat_id=message.chat.id, chat_title=chat_title
            )
            await message.reply("그룹 재장전 실패")
    except Exception as e:
        logger.error("reload_group_exception", chat_id=message.chat.id, error=str(e))
        await message.reply(f"그룹 재장전 중 오류 발생: {str(e)}")


@router.message(Command(commands=["grouplist", "그룹목록"], prefix="."))
async def list_groups(message: types.Message) -> None:
    """그룹 목록 명령어 (.그룹목록)."""
    logger.info(
        "list_groups_triggered",
        user_id=message.from_user.id if message.from_user else None,
        chat_id=message.chat.id,
        text=message.text,
    )

    if not message.from_user:
        logger.error("list_groups_error", error="No user information")
        await message.reply("사용자 정보를 확인할 수 없습니다.")
        return

    is_admin_result = await is_admin(message.from_user.id)
    logger.info(
        "permission_check", user_id=message.from_user.id, is_admin=is_admin_result
    )

    if not is_admin_result:
        logger.warning(
            "permission_denied", user_id=message.from_user.id, chat_id=message.chat.id
        )
        await message.reply("관리자만 사용 가능합니다.")
        return

    try:
        groups = await get_groups()
        logger.info("groups_fetched", group_count=len(groups))
        if not groups:
            await message.reply("등록된 그룹이 없습니다.")
            logger.info(
                "reply_sent",
                chat_id=message.chat.id,
                message="등록된 그룹이 없습니다.",
            )
            return

        response = "📋 등록된 그룹 목록:\n"
        for chat_id, info in groups.items():
            muted_status = "음소거" if info.get("muted", False) else "알림 활성"
            response += f"- {info['title']} (ID: {chat_id}, 상태: {muted_status})\n"
        await message.reply(response)
        logger.info("reply_sent", chat_id=message.chat.id, message="그룹 목록 출력")
    except Exception as e:
        logger.error("list_groups_exception", chat_id=message.chat.id, error=str(e))
        await message.reply(f"그룹 목록 조회 중 오류 발생: {str(e)}")


@router.message(Command(commands=["groupdelete", "그룹삭제"], prefix="."))
async def delete_group(message: types.Message, bot: Bot) -> None:
    """그룹 삭제 명령어 (.그룹삭제)."""
    logger.info(
        "delete_group_triggered",
        user_id=message.from_user.id if message.from_user else None,
        chat_id=message.chat.id,
        text=message.text,
    )

    if not message.from_user:
        logger.error("delete_group_error", error="No user information")
        await message.reply("사용자 정보를 확인할 수 없습니다.")
        return

    is_admin_result = await is_admin(message.from_user.id)
    logger.info(
        "permission_check", user_id=message.from_user.id, is_admin=is_admin_result
    )

    if not is_admin_result:
        logger.warning(
            "permission_denied", user_id=message.from_user.id, chat_id=message.chat.id
        )
        await message.reply("관리자만 사용 가능합니다.")
        return

    if not message.text:
        await message.reply("그룹 ID를 입력하세요. 예: .그룹삭제 123456")
        return

    text = message.text.split()
    if len(text) < 2 or not text[1].lstrip("-").isdigit():
        await message.reply("유효한 그룹 ID를 입력하세요. 예: .그룹삭제 -123456")
        return

    chat_id = int(text[1])
    try:
        groups = await get_groups()
        if str(chat_id) not in groups:
            await message.reply(f"그룹 ID {chat_id}가 등록되어 있지 않습니다.")
            return

        title = groups[str(chat_id)]["title"]
        if await remove_group(chat_id):
            await log_group_remove(
                bot,
                title,
                chat_id,
                message.from_user.id,
                message.from_user.username or "Unknown",
            )
            await message.reply(f"그룹 '{title}' 삭제 완료")
            logger.info("reply_sent", chat_id=message.chat.id, message="그룹 삭제 완료")
        else:
            await message.reply("그룹 삭제 실패")
    except Exception as e:
        logger.error("delete_group_exception", chat_id=message.chat.id, error=str(e))
        await message.reply(f"그룹 삭제 중 오류 발생: {str(e)}")

from aiogram import Router, types
from aiogram.filters import Command, CommandStart

from config import logger
from database.users import add_admin, remove_admin
from utils.logger import log_admin_add, log_admin_remove
from utils.permissions import is_admin

router = Router()


@router.message(CommandStart())
async def start_cmd(message: types.Message):
    """봇 시작 명령어 (.start)."""
    logger.info(
        "start_cmd_triggered",
        user_id=message.from_user.id if message.from_user else None,
        chat_id=message.chat.id,
    )
    if not message.from_user:
        logger.error("start_cmd_error", error="No user information")
        try:
            await message.reply("사용자 정보를 확인할 수 없습니다.")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
        return
    if await is_admin(message.from_user.id):
        try:
            await message.reply("관리자님, 환영합니다!")
            logger.info(
                "reply_sent", chat_id=message.chat.id, message="관리자님, 환영합니다!"
            )
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
    else:
        try:
            await message.reply("환영합니다! 명령어를 확인하려면 .help를 입력하세요.")
            logger.info("reply_sent", chat_id=message.chat.id, message="환영합니다!")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))


@router.message(Command(commands=["ad"], prefix="."))
async def add_admin_cmd(message: types.Message, bot):
    """관리자 추가 명령어 (.ad)."""
    logger.info(
        "add_admin_cmd_triggered",
        user_id=message.from_user.id if message.from_user else None,
        chat_id=message.chat.id,
        text=message.text,
    )

    if not message.from_user:
        logger.error("add_admin_cmd_error", error="No user information")
        try:
            await message.reply("사용자 정보를 확인할 수 없습니다.")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
        return

    if not await is_admin(message.from_user.id):
        logger.warning(
            "permission_denied", user_id=message.from_user.id, chat_id=message.chat.id
        )
        try:
            await message.reply("권한이 없습니다.")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
        return

    if not message.text:
        try:
            await message.reply("명령어 형식이 잘못되었습니다. 예: .ad 123456")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        try:
            await message.reply("사용자 ID를 입력하세요. 예: .ad 123456")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
        return

    target_id = int(args[1])
    try:
        success = await add_admin(
            target_id,
            "Unknown",  # 사용자 이름은 실제 구현에 따라 가져오기
            message.from_user.id,
            message.from_user.username or "Unknown",
        )
        if success:
            logger.info(
                "admin_added", target_id=target_id, added_by=message.from_user.id
            )
            try:
                await message.reply(f"사용자 {target_id}가 관리자로 추가되었습니다.")
                logger.info(
                    "reply_sent", chat_id=message.chat.id, message="관리자 추가 완료"
                )
                await log_admin_add(
                    bot,
                    target_id,
                    "Unknown",
                    message.from_user.id,
                    message.from_user.username or "Unknown",
                )
            except Exception as e:
                logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
        else:
            logger.error("add_admin_failed", target_id=target_id)
            try:
                await message.reply("관리자 추가 실패")
            except Exception as e:
                logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
    except Exception as e:
        logger.error("add_admin_cmd_exception", target_id=target_id, error=str(e))
        try:
            await message.reply(f"관리자 추가 중 오류 발생: {str(e)}")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))


@router.message(Command(commands=["unad"], prefix="."))
async def remove_admin_cmd(message: types.Message, bot):
    """관리자 제거 명령어 (.unad)."""
    logger.info(
        "remove_admin_cmd_triggered",
        user_id=message.from_user.id if message.from_user else None,
        chat_id=message.chat.id,
        text=message.text,
    )

    if not message.from_user:
        logger.error("remove_admin_cmd_error", error="No user information")
        try:
            await message.reply("사용자 정보를 확인할 수 없습니다.")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
        return

    if not await is_admin(message.from_user.id):
        logger.warning(
            "permission_denied", user_id=message.from_user.id, chat_id=message.chat.id
        )
        try:
            await message.reply("권한이 없습니다.")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
        return

    if not message.text:
        try:
            await message.reply("명령어 형식이 잘못되었습니다. 예: .unad 123456")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
        return

    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        try:
            await message.reply("사용자 ID를 입력하세요. 예: .unad 123456")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
        return

    target_id = int(args[1])
    try:
        success = await remove_admin(target_id)
        if success:
            logger.info(
                "admin_removed", target_id=target_id, removed_by=message.from_user.id
            )
            try:
                await message.reply(f"사용자 {target_id}가 관리자에서 제거되었습니다.")
                logger.info(
                    "reply_sent", chat_id=message.chat.id, message="관리자 제거 완료"
                )
                await log_admin_remove(
                    bot,
                    target_id,
                    "Unknown",
                    message.from_user.id,
                    message.from_user.username or "Unknown",
                )
            except Exception as e:
                logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
        else:
            logger.error("remove_admin_failed", target_id=target_id)
            try:
                await message.reply("관리자 제거 실패")
            except Exception as e:
                logger.error("reply_failed", chat_id=message.chat.id, error=str(e))
    except Exception as e:
        logger.error("remove_admin_cmd_exception", target_id=target_id, error=str(e))
        try:
            await message.reply(f"관리자 제거 중 오류 발생: {str(e)}")
        except Exception as e:
            logger.error("reply_failed", chat_id=message.chat.id, error=str(e))

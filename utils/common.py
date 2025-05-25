from typing import Any, Dict, List, Optional, Tuple

from aiogram import Bot, types

from config import logger
from database.username_cache import cache_username, get_user_id_from_cache


async def extract_user_info(message: types.Message, bot: Bot) -> Dict[str, Any]:
    """메시지에서 사용자 정보 추출."""
    user_info: Dict[str, Any] = {
        "user_id": 0,
        "username": "",
        "reason": "",
        "user_ids": [],
    }

    try:
        # 답장 메시지 처리
        if message.reply_to_message and message.reply_to_message.from_user:
            user = message.reply_to_message.from_user
            user_info["user_id"] = user.id
            # 사용자명 또는 HTML 태그로 감싼 성과 이름
            if user.username:
                user_info["username"] = user.username
            else:
                full_name = f"{user.first_name} {user.last_name}".strip()
                user_info["username"] = (
                    f"<b>{full_name}</b>" if full_name else "<b>Nickname</b>"
                )
            await cache_username(user.id, user_info["username"])

        # 텍스트 인자 처리
        elif message.text:
            text = message.text.split(maxsplit=1)
            if len(text) > 1:
                args = text[1].split()
                reason_start = 0

                # 사용자 ID 또는 사용자명 처리
                for arg in args:
                    if arg.isdigit():
                        user_info["user_ids"].append(int(arg))
                        reason_start += 1
                    elif arg.startswith("@"):
                        user_id = await get_user_id_from_cache(arg)
                        if user_id:
                            user_info["user_ids"].append(user_id)
                        reason_start += 1
                    else:
                        break

                # 사유 추출
                if reason_start < len(args):
                    user_info["reason"] = " ".join(args[reason_start:])

        return user_info

    except Exception as e:
        logger.error("extract_user_info_failed", chat_id=message.chat.id, error=str(e))
        return user_info

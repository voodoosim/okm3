import os
from typing import List
from dotenv import load_dotenv
import structlog
import logging

load_dotenv('c:/abb/.env')

BOT_TOKEN: str = os.getenv("BOT_TOKEN") or ""
if not BOT_TOKEN.strip():
    raise ValueError("BOT_TOKEN 환경 변수가 설정되지 않았거나 비어 있습니다.")

MASTER_ADMIN_IDS: List[int] = []
admin_ids_str = os.getenv("MASTER_ADMIN_IDS")
if admin_ids_str:
    MASTER_ADMIN_IDS = [
        int(id.strip())
        for id in admin_ids_str.split(",")
        if id.strip() and id.strip().isdigit()
    ]

def get_channel_id(key: str) -> int:
    value = os.getenv(key)
    if value and value.strip() and value.strip().startswith('-') and value.strip()[1:].isdigit():
        return int(value.strip())
    raise ValueError(f"{key} 환경 변수가 유효한 채널 ID가 아닙니다: {value}")

LOG_CHANNEL_ID = get_channel_id("LOG_CHANNEL_ID")
PUBLIC_LOG_CHANNEL_ID = get_channel_id("PUBLIC_LOG_CHANNEL_ID")

DATA_DIR = "data"
GROUPS_FILE = os.path.join(DATA_DIR, "groups.json")
BANNED_USERS_FILE = os.path.join(DATA_DIR, "banned_users.json")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.json")

os.makedirs(DATA_DIR, exist_ok=True)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()],
)
logger = structlog.get_logger()

def is_valid_config() -> bool:
    if not BOT_TOKEN:
        logger.error("config_validation_failed", error="BOT_TOKEN is not set")
        return False
    if not MASTER_ADMIN_IDS:
        logger.error("config_validation_failed", error="MASTER_ADMIN_IDS is not set")
        return False
    return True

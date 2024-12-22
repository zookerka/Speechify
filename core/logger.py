
from logtail import LogtailHandler
import logging
from .config import LOG_TOKEN

log_handler = LogtailHandler(source_token=LOG_TOKEN)
logger = logging.getLogger("bot_logger")
logger.setLevel(logging.INFO)
logger.handlers = []
logger.addHandler(log_handler)

"""日志配置：脱敏、不记录 Authorization Header / Base64 图片 / 聊天原文。"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from ..infrastructure.config_store import get_app_data_dir

_SENSITIVE_KEYS = {"authorization", "api_key", "apikey", "api-key"}


def _sanitize(record: logging.LogRecord) -> logging.LogRecord:
    """简单脱敏：去掉消息中可能出现的敏感字段。"""
    msg = record.getMessage()
    for key in _SENSITIVE_KEYS:
        if key in msg.lower():
            msg = msg.replace(key, "***")
    record.msg = msg
    record.args = ()
    return record


class SanitizingFormatter(logging.Formatter):
    def format(self, record):
        record = _sanitize(record)
        return super().format(record)


def get_log_dir() -> Path:
    d = get_app_data_dir() / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("lolchattranslator")
    if logger.handlers:
        return logger
    logger.setLevel(level)

    fmt = SanitizingFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    # 控制台（仅在存在可用的 stdout 时添加；windowed 打包模式下 sys.stdout 为 None）
    try:
        if sys.stdout is not None:
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(fmt)
            logger.addHandler(sh)
    except Exception:
        pass

    # 文件（轮转，避免无限增长）
    try:
        logfile = get_log_dir() / "app.log"
        fh = RotatingFileHandler(logfile, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass

    return logger


def get_logger() -> logging.Logger:
    return logging.getLogger("lolchattranslator")

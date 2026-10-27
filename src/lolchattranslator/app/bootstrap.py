"""启动引导：初始化 QApplication、单实例检查、启动 Application。"""
import sys

from PySide6.QtWidgets import QApplication

from ..infrastructure.logging_config import get_logger
from .application import Application
from .lifecycle import acquire_single_instance

logger = get_logger()


def bootstrap() -> int:
    """程序入口，返回退出码。"""
    # 单实例检查
    if not acquire_single_instance():
        logger.warning("检测到已有实例运行，退出")
        return 0

    qapp = QApplication(sys.argv)
    qapp.setApplicationName("LOL国际服聊天框翻译")
    qapp.setOrganizationName("LoLChatTranslator")

    app = Application(qapp)
    app.run()

    exit_code = qapp.exec()
    app.shutdown()
    return exit_code

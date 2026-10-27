"""应用生命周期管理：单实例锁 + 资源初始化/清理。"""
import os
import sys

from ..infrastructure.config_store import get_app_data_dir
from ..infrastructure.logging_config import get_logger

logger = get_logger()

_instance_lock_fd = None


def acquire_single_instance() -> bool:
    """尝试获取单实例文件锁，若已有实例运行则返回 False。"""
    global _instance_lock_fd
    try:
        lock_path = get_app_data_dir() / ".instance.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            return False
        _instance_lock_fd = fd
        return True
    except Exception:
        return True


def release_single_instance():
    global _instance_lock_fd
    if _instance_lock_fd is not None:
        try:
            os.close(_instance_lock_fd)
        except Exception:
            pass
        _instance_lock_fd = None

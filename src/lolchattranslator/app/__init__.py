"""应用包。"""
from .application import Application
from .task_manager import TaskManager

__all__ = ["Application", "TaskManager"]


def main():
    """控制台入口。"""
    from .bootstrap import bootstrap

    raise SystemExit(bootstrap())

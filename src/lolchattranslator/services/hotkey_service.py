"""全局快捷键管理：基于 keyboard 库，带冲突检测、去抖与恢复默认。

注意：keyboard 库的全局钩子回调运行在独立线程，本模块只负责注册/触发，
回调内部只投递动作名，由 UI 线程通过信号槽消费。
"""
import time
from collections.abc import Callable

from ..infrastructure.logging_config import get_logger

logger = get_logger()

# 默认快捷键
DEFAULT_HOTKEYS = {
    "capture_translate": "f6",
    "retranslate": "f7",
    "copy_last": "f8",
    "toggle_window": "home",
    "select_region": "f9",
    "reply_translate": "f10",
    "cancel": "esc",
}

# 可选的键名（供设置界面下拉使用）
AVAILABLE_KEYS = [
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
    "home", "end", "insert", "delete", "page up", "page down",
    "ctrl+alt+t", "ctrl+alt+y", "ctrl+alt+c", "ctrl+alt+h", "ctrl+alt+r",
]

# 去抖时间（秒）
DEBOUNCE_SECONDS = 0.35


class HotkeyManager:
    def __init__(self):
        self._keyboard = None
        self._handlers: dict[str, Callable] = {}
        self._registered: dict[str, str] = {}
        self._last_trigger: dict[str, float] = {}
        self._active = False

    def _get_keyboard(self):
        if self._keyboard is None:
            import keyboard

            self._keyboard = keyboard
        return self._keyboard

    def register_all(self, mapping: dict[str, str], handlers: dict[str, Callable]) -> list[str]:
        warnings = []
        self.unregister_all()
        self._handlers = handlers

        # 冲突检测
        reverse: dict[str, str] = {}
        for action, hotkey in mapping.items():
            if not hotkey:
                continue
            if hotkey in reverse:
                warnings.append(f"快捷键冲突：'{hotkey}' 同时分配给 '{reverse[hotkey]}' 和 '{action}'")
                continue
            reverse[hotkey] = action

        kb = self._get_keyboard()
        for action, hotkey in mapping.items():
            if not hotkey:
                continue
            if hotkey in reverse and reverse[hotkey] != action:
                continue
            handler = handlers.get(action)
            if not handler:
                continue
            try:
                kb.add_hotkey(hotkey, self._make_debounced(handler, action))
                self._registered[action] = hotkey
            except Exception as e:
                warnings.append(f"注册快捷键 '{hotkey}' 失败: {e}")

        self._active = True
        return warnings

    def _make_debounced(self, fn: Callable, action: str):
        def wrapper():
            now = time.monotonic()
            last = self._last_trigger.get(action, 0)
            if now - last < DEBOUNCE_SECONDS:
                return
            self._last_trigger[action] = now
            try:
                fn()
            except Exception as e:
                logger.warning("快捷键回调异常: %s", e)

        return wrapper

    def unregister_all(self) -> None:
        if self._keyboard is not None:
            try:
                self._keyboard.unhook_all_hotkeys()
            except Exception:
                pass
        self._registered.clear()
        self._last_trigger.clear()
        self._active = False

    @staticmethod
    def detect_conflicts(mapping: dict[str, str]) -> list[str]:
        reverse: dict[str, str] = {}
        warnings = []
        for action, hotkey in mapping.items():
            if not hotkey:
                continue
            if hotkey in reverse:
                warnings.append(f"'{hotkey}' 冲突：{reverse[hotkey]} 与 {action}")
            else:
                reverse[hotkey] = action
        return warnings

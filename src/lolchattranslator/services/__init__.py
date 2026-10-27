"""服务包。"""
from .hotkey_service import AVAILABLE_KEYS, DEFAULT_HOTKEYS, HotkeyManager
from .image_processor import ImageProcessor
from .input_injector import InputInjector
from .screenshot_service import ScreenshotError, ScreenshotService
from .tray_service import TrayService

__all__ = [
    "ImageProcessor",
    "InputInjector",
    "ScreenshotError",
    "ScreenshotService",
    "AVAILABLE_KEYS",
    "DEFAULT_HOTKEYS",
    "HotkeyManager",
    "TrayService",
]

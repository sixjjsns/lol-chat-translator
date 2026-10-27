"""系统托盘服务：图标 + 菜单。

使用 pystray 在独立线程运行，菜单回调通过 Qt 信号安全回传主线程。
"""
import os
import sys
import threading

from ..infrastructure.logging_config import get_logger

logger = get_logger()


def _asset_path(name: str) -> str:
    """定位资源文件（兼容打包后的 _MEIPASS）。"""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, "resources", "icons", name)
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "resources", "icons", name,
    )


def _make_icon_image():
    """加载应用图标；找不到时用 Pillow 绘制兜底图标。"""
    from PIL import Image, ImageDraw

    png = _asset_path("app_icon.png")
    if os.path.exists(png):
        try:
            img = Image.open(png)
            if img.mode != "RGBA":
                img = img.convert("RGBA")
            return img
        except Exception:
            pass
    # 兜底：绿色对话气泡
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 8, 60, 52], radius=10, fill=(40, 160, 80, 255))
    d.polygon([(14, 44), (10, 58), (28, 48)], fill=(40, 160, 80, 255))
    d.ellipse([16, 18, 24, 26], fill=(255, 255, 255, 255))
    d.ellipse([30, 18, 38, 26], fill=(255, 255, 255, 255))
    d.ellipse([44, 18, 52, 26], fill=(255, 255, 255, 255))
    return img


class TrayService:
    def __init__(self, menu_actions: dict, on_quit=None):
        self.menu_actions = menu_actions  # {label: callable}
        self.on_quit = on_quit
        self.icon = None
        self._thread = None

    def start(self):
        import pystray

        icon = pystray.Icon(
            "lolchattranslator",
            _make_icon_image(),
            "LoL 聊天翻译",
            menu=self._build_menu(),
        )
        self.icon = icon
        self._thread = threading.Thread(target=icon.run, daemon=True)
        self._thread.start()

    def _build_menu(self):
        import pystray

        items = []
        for label, fn in self.menu_actions.items():
            if fn is None:
                items.append(pystray.Menu.SEPARATOR)
            else:
                items.append(pystray.MenuItem(label, self._wrap(fn)))
        items.append(pystray.Menu.SEPARATOR)
        items.append(pystray.MenuItem("退出", self._wrap(self.on_quit)))
        return pystray.Menu(*items)

    @staticmethod
    def _wrap(fn):
        def _inner(icon=None, item=None):
            try:
                fn()
            except Exception:
                pass

        return _inner

    def stop(self):
        if self.icon is not None:
            try:
                self.icon.stop()
            except Exception:
                pass
            self.icon = None

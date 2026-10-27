"""主窗口：侧边导航 + 页面容器 + 状态栏。"""
import os
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from .i18n import set_language, tr
from .pages.settings_page import SettingsPage
from .pages.translation_page import TranslationPage
from .theme import build_stylesheet


def _asset_path(name: str) -> str:
    """定位资源文件（兼容打包后的 _MEIPASS）。"""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, "resources", "icons", name)
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "resources", "icons", name,
    )


class MainWindow(QMainWindow):
    """应用主窗口。"""

    # 信号：转交给 App 层处理
    replyRequested = Signal(str, str)
    naturalnessChanged = Signal(int)
    selectRegionRequested = Signal()
    captureRequested = Signal()
    copyRequested = Signal()
    saveSettingsRequested = Signal(dict)
    testConnectionRequested = Signal(dict)
    clearKeyRequested = Signal()

    def __init__(self, providers: dict, settings, api_key: str = "", parent=None):
        super().__init__(parent)
        self._providers = providers
        self._settings = settings
        self._api_key = api_key
        self.setWindowTitle("LoL Chat Translator")
        self.resize(880, 680)
        self.setMinimumSize(700, 540)
        self._apply_icon()
        self._apply_style()
        self._build_ui()

    def _apply_icon(self):
        ico = _asset_path("app_icon.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

    def _apply_style(self):
        self.setStyleSheet(build_stylesheet())

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 侧边导航
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(150)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(12, 16, 12, 16)
        side_layout.setSpacing(8)

        app_title = QLabel("LoL 翻译")
        app_title.setObjectName("appTitle")
        side_layout.addWidget(app_title)

        self.nav_translate = QPushButton("🖥  翻译")
        self.nav_settings = QPushButton("⚙  设置")
        for btn in (self.nav_translate, self.nav_settings):
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.nav_translate.setChecked(True)
        side_layout.addWidget(self.nav_translate)
        side_layout.addWidget(self.nav_settings)
        side_layout.addStretch(1)

        # 侧边栏底部提示
        hint = QLabel("v0.1.0")
        hint.setObjectName("sidebarHint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        side_layout.addWidget(hint)

        root.addWidget(sidebar)

        # 页面容器
        self.stack = QStackedWidget()
        self.translation_page = TranslationPage()
        self.settings_page = SettingsPage(self._providers, self._settings)
        self.settings_page.set_api_key(self._api_key)
        self.stack.addWidget(self.translation_page)
        self.stack.addWidget(self.settings_page)
        root.addWidget(self.stack)

        # 导航切换
        self.nav_translate.clicked.connect(lambda: self._switch_page(0))
        self.nav_settings.clicked.connect(lambda: self._switch_page(1))

        # 状态栏
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("就绪 · 按 F6 截图翻译")

        # 转发页面信号
        self.translation_page.replyRequested.connect(self.replyRequested.emit)
        self.translation_page.naturalnessChanged.connect(self.naturalnessChanged.emit)
        self.translation_page.selectRegionRequested.connect(self.selectRegionRequested.emit)
        self.translation_page.captureRequested.connect(self.captureRequested.emit)
        self.settings_page.saveRequested.connect(self.saveSettingsRequested.emit)
        self.settings_page.testRequested.connect(self.testConnectionRequested.emit)
        self.settings_page.keyCleared.connect(self.clearKeyRequested.emit)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.nav_translate.setChecked(index == 0)
        self.nav_settings.setChecked(index == 1)

    # --- 供 App 层调用 ---
    def apply_language(self, lang: str):
        """切换界面语言并刷新所有文案。"""
        set_language(lang)
        # 导航
        self.nav_translate.setText(tr("nav.translate"))
        self.nav_settings.setText(tr("nav.settings"))
        # 页面
        self.translation_page.apply_language()
        self.settings_page.apply_language()
        # 状态栏
        self.status.showMessage(tr("status.ready"))

    def show_settings(self):
        self._switch_page(1)

    def set_status(self, text: str):
        self.status.showMessage(text)

    def set_result(self, text: str):
        self.translation_page.set_result(text)

    def set_reply_result(self, text: str):
        self.translation_page.set_reply_result(text)

    def show_error(self, text: str):
        self.status.showMessage(text)
        self.set_status(text)

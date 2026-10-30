"""主窗口：品牌侧边栏 + 顶栏 + 页面容器 + 状态栏（v1.2.0 重制）。

视觉结构
--------
::

    ┌──────────────┬──────────────────────────────────────────────┐
    │ [icon] LoL 翻译 │ 翻译                      [智谱 GLM-4V] [注入·开] │
    │ Chat Translator│                                              │
    │                │  ┌────────────────────────────────────────┐  │
    │ 工作区          │  │  页面内容（翻译 / 设置）                 │  │
    │  🖥 翻译        │  │                                        │  │
    │  ⚙ 设置        │  └────────────────────────────────────────┘  │
    │                │                                              │
    │ ┌────────────┐ │                                              │
    │ │ 快捷键      │ │                                              │
    │ │ F6 截图翻译 │ │                                              │
    │ │ F10 翻译注入│ │                                              │
    │ └────────────┘ │                                              │
    │ v1.2.0          │                                              │
    └──────────────┴──────────────────────────────────────────────┘

侧边栏承载“常驻信息”（快捷键、版本），顶栏承载“当前状态”（服务、注入开关），
正文只放操作与内容，三者职责不重叠。
"""

from __future__ import annotations

import os
import sys

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPainter, QPainterPath, QPixmap
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

APP_VERSION = "1.2.0"


def _asset_path(name: str) -> str:
    """定位资源文件（兼容打包后的 _MEIPASS）。"""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, "resources", "icons", name)
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "resources", "icons", name,
    )


def _rounded_pixmap(path: str, size: int, radius: int) -> QPixmap:
    """把图标裁成圆角，避免小尺寸下方形边缘显得脏。"""
    src = QPixmap(path)
    if src.isNull():
        return QPixmap()
    scaled = src.scaled(
        size, size,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    out = QPixmap(size, size)
    out.fill(Qt.GlobalColor.transparent)
    painter = QPainter(out)
    painter.setRenderHints(
        QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
    )
    clip = QPainterPath()
    clip.addRoundedRect(0, 0, size, size, radius, radius)
    painter.setClipPath(clip)
    painter.drawPixmap(0, 0, scaled)
    painter.end()
    return out


def _apply_dark_titlebar(widget) -> None:
    """让 Windows 11 的标题栏跟随深色主题（失败也不影响功能）。"""
    try:
        import ctypes

        hwnd = int(widget.winId())
        enabled = ctypes.c_int(1)
        for attribute in (20, 19):  # 20=Win10 20H1+，19=更早
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(enabled), ctypes.sizeof(enabled)
            ) == 0:
                break
    except Exception:
        pass


class MainWindow(QMainWindow):
    """应用主窗口。"""

    # 信号：转交给 App 层处理
    replyRequested = Signal(str, str)
    naturalnessChanged = Signal(int)
    selectRegionRequested = Signal()
    captureRequested = Signal()
    retranslateRequested = Signal()
    copyRequested = Signal()
    saveSettingsRequested = Signal(dict)
    testConnectionRequested = Signal(dict)
    clearKeyRequested = Signal()

    def __init__(self, providers: dict, settings, api_key: str = "", parent=None):
        super().__init__(parent)
        self._providers = providers
        self._settings = settings
        self._api_key = api_key
        self.setWindowTitle(tr("app.title"))
        self.resize(1020, 740)
        self.setMinimumSize(940, 660)
        self._apply_icon()
        self._apply_style()
        self._build_ui()

    # ------------------------------------------------------------------
    def showEvent(self, event):  # noqa: N802 (Qt 命名)
        super().showEvent(event)
        if not getattr(self, "_titlebar_done", False):
            self._titlebar_done = True
            _apply_dark_titlebar(self)

    def _apply_icon(self):
        ico = _asset_path("app_icon.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

    def _apply_style(self):
        self.setStyleSheet(build_stylesheet())

    # ------------------------------------------------------------------
    def _build_ui(self):
        central = QWidget()
        central.setObjectName("appRoot")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        right.addWidget(self._build_topbar())

        self.stack = QStackedWidget()
        self.translation_page = TranslationPage()
        self.settings_page = SettingsPage(self._providers, self._settings)
        self.settings_page.set_api_key(self._api_key)
        self.stack.addWidget(self.translation_page)
        self.stack.addWidget(self.settings_page)
        right.addWidget(self.stack, 1)

        right_wrap = QWidget()
        right_wrap.setLayout(right)
        root.addWidget(right_wrap, 1)

        self._connect_page_signals()

        # 状态栏
        self.status = QStatusBar()
        self.status.setSizeGripEnabled(False)
        self.setStatusBar(self.status)
        self.status.showMessage(tr("status.ready"))

    # ------------------------------------------------------------------
    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(212)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 18, 16, 16)
        layout.setSpacing(8)

        # 品牌区
        brand = QHBoxLayout()
        brand.setSpacing(10)

        logo = QLabel()
        png = _asset_path("app_icon.png")
        if os.path.exists(png):
            logo.setPixmap(_rounded_pixmap(png, 40, 11))
        logo.setFixedSize(40, 40)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        self.brand_name = QLabel(tr("app.brand"))
        self.brand_name.setObjectName("brandName")
        self.brand_sub = QLabel("CHAT TRANSLATOR")
        self.brand_sub.setObjectName("brandSub")
        brand_text.addWidget(self.brand_name)
        brand_text.addWidget(self.brand_sub)

        brand.addWidget(logo)
        brand.addLayout(brand_text)
        brand.addStretch(1)
        layout.addLayout(brand)
        layout.addSpacing(14)

        # 导航
        nav_section = QLabel(tr("nav.section"))
        nav_section.setObjectName("navSection")
        layout.addWidget(nav_section)

        self.nav_translate = QPushButton("🖥   " + tr("nav.translate"))
        self.nav_settings = QPushButton("⚙   " + tr("nav.settings"))
        for btn in (self.nav_translate, self.nav_settings):
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(38)
        self.nav_translate.setChecked(True)
        layout.addWidget(self.nav_translate)
        layout.addWidget(self.nav_settings)
        layout.addStretch(1)

        # 快捷键卡片
        layout.addWidget(self._build_hotkey_card())

        self.version_label = QLabel(f"v{APP_VERSION}")
        self.version_label.setObjectName("brandSub")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.version_label)

        self.nav_translate.clicked.connect(lambda: self._switch_page(0))
        self.nav_settings.clicked.connect(lambda: self._switch_page(1))
        return sidebar

    def _build_hotkey_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("sideCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 12)
        layout.setSpacing(6)

        title = QLabel("SHORTCUTS")
        title.setObjectName("sideCardTitle")
        layout.addWidget(title)

        self._hotkey_value_labels: dict[str, QLabel] = {}
        for action, default in (
            ("capture_translate", "F6"),
            ("reply_translate", "F10"),
            ("retranslate", "F7"),
            ("copy_last", "F8"),
        ):
            row = QHBoxLayout()
            row.setSpacing(6)
            key = QLabel(default)
            key.setObjectName("sideCardValue")
            key.setFixedWidth(38)
            label = QLabel(tr(f"hotkey.{action}"))
            label.setObjectName("sideCardKey")
            row.addWidget(key)
            row.addWidget(label, 1)
            layout.addLayout(row)
            self._hotkey_value_labels[action] = key

        return card

    def _build_topbar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("topBar")
        bar.setFixedHeight(70)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(10)

        titles = QVBoxLayout()
        titles.setSpacing(1)
        self.page_title = QLabel(tr("page.translate.title"))
        self.page_title.setObjectName("pageTitle")
        self.page_subtitle = QLabel(tr("page.translate.subtitle"))
        self.page_subtitle.setObjectName("pageSubtitle")
        titles.addWidget(self.page_title)
        titles.addWidget(self.page_subtitle)
        layout.addLayout(titles)
        layout.addStretch(1)

        self.provider_chip = QLabel("—")
        self.provider_chip.setObjectName("chip")
        self.provider_chip.setFixedHeight(28)
        self.provider_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inject_chip = QLabel(tr("chip.inject_off"))
        self.inject_chip.setObjectName("chip")
        self.inject_chip.setFixedHeight(28)
        self.inject_chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inject_chip.setToolTip(tr("tip.inject_state"))

        layout.addWidget(self.provider_chip)
        layout.addWidget(self.inject_chip)
        return bar

    # ------------------------------------------------------------------
    def _connect_page_signals(self):
        page = self.translation_page
        page.replyRequested.connect(self.replyRequested.emit)
        page.naturalnessChanged.connect(self.naturalnessChanged.emit)
        page.selectRegionRequested.connect(self.selectRegionRequested.emit)
        page.captureRequested.connect(self.captureRequested.emit)
        page.retranslateRequested.connect(self.retranslateRequested.emit)
        page.copyRequested.connect(self.copyRequested.emit)

        settings = self.settings_page
        settings.saveRequested.connect(self.saveSettingsRequested.emit)
        settings.testRequested.connect(self.testConnectionRequested.emit)
        settings.keyCleared.connect(self.clearKeyRequested.emit)

    def _switch_page(self, index: int):
        self.stack.setCurrentIndex(index)
        self.nav_translate.setChecked(index == 0)
        self.nav_settings.setChecked(index == 1)
        if index == 0:
            self.set_page_header("page.translate.title", "page.translate.subtitle")
        else:
            self.set_page_header("page.settings.title", "page.settings.subtitle")

    def set_page_header(self, title_key: str, subtitle_key: str):
        self.page_title.setText(tr(title_key))
        self.page_subtitle.setText(tr(subtitle_key))

    # --- 供 App 层调用 ---
    def apply_language(self, lang: str):
        """切换界面语言并刷新所有文案。"""
        set_language(lang)
        self.brand_name.setText(tr("app.brand"))
        self.nav_translate.setText("🖥   " + tr("nav.translate"))
        self.nav_settings.setText("⚙   " + tr("nav.settings"))
        self.translation_page.apply_language()
        self.settings_page.apply_language()
        self.set_auto_paste_state(self.inject_chip.objectName() == "chipOk")
        self._switch_page(self.stack.currentIndex())
        self.status.showMessage(tr("status.ready"))

    def set_provider_text(self, text: str):
        self.provider_chip.setText(text or "—")

    def set_auto_paste_state(self, enabled: bool):
        self.inject_chip.setText(tr("chip.inject_on") if enabled else tr("chip.inject_off"))
        self.inject_chip.setObjectName("chipOk" if enabled else "chip")
        self.inject_chip.style().unpolish(self.inject_chip)
        self.inject_chip.style().polish(self.inject_chip)
        self.translation_page.set_auto_paste(enabled)

    def set_region_state(self, has_region: bool):
        self.translation_page.set_region_state(has_region)

    def set_busy(self, busy: bool):
        self.translation_page.set_busy(busy)

    def set_duration(self, detail: str):
        self.translation_page.set_duration(detail)

    def set_hotkey_labels(self, mapping: dict):
        """把当前生效的快捷键显示到侧边栏（保存设置后调用）。"""
        for action, label in self._hotkey_value_labels.items():
            value = (mapping or {}).get(action)
            if value:
                label.setText(str(value).upper())

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

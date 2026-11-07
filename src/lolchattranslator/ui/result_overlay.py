"""译文阅读悬浮窗（v1.2.1 重写）：不挡操作、任意位置可拖、绝不跑出屏幕。

v1.2.1 修复的问题
----------------
1. **拖不动**：旧版正文 QLabel 开了 `TextSelectableByMouse`，把鼠标按下事件吃掉了，
   只有标题栏和边距那几像素能拖。现在正文不再抢鼠标事件，**按住窗口任意位置都能拖**，
   复制译文移到右键菜单里。
2. **译文跑出屏幕**：旧版先定位再 `adjustSize()`，窗口变大后下半截就伸到屏幕外；
   而且长译文时窗口宽度超过屏幕。现在先调整尺寸、限制最大宽高，再把窗口**钳制在
   屏幕可用区域内**，四个角都不会越界。
3. **挡住鼠标互动**：新增
   - 自动隐藏（默认 15 秒，鼠标悬停时暂停计时，移开重新计时；0 = 常驻）；
   - 右键菜单「鼠标穿透」：开启后点击直接穿过窗口落到游戏里（此时靠 F11 关闭）；
   - 全局快捷键 **F11** 隐藏/呼出（由 App 层实现）。
"""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

MARGIN = 16
MIN_WIDTH = 220
MAX_WIDTH_RATIO = 0.42
MAX_HEIGHT_RATIO = 0.38


class ResultOverlayWindow(QWidget):
    """译文阅读悬浮窗口（F6 截图翻译结果，只读）。"""

    closed = Signal()

    def __init__(self, display_duration: int = 15, parent=None):
        super().__init__(parent)
        self._display_duration = max(0, int(display_duration))
        self._position = "bottom-right"
        self._penetrate = False
        self._drag_offset = None
        self._user_moved = False
        self._last_text = ""
        self._last_detail = ""

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setMouseTracking(True)

        # 自动隐藏定时器（悬停暂停）
        self._auto_hide = QTimer(self)
        self._auto_hide.setSingleShot(True)
        self._auto_hide.timeout.connect(self.hide)

        self._build_ui()
        # v1.2.3：默认更小，少挡画面
        self.resize(340, 136)

    # ------------------------------------------------------------------
    def _build_ui(self):
        self.setObjectName("overlayRoot")
        self.setStyleSheet("""
            QWidget#overlayRoot {
                background-color: rgba(13, 21, 32, 240);
                border: 1px solid #c9a24b;
                border-radius: 10px;
            }
            QLabel#overlayTitle {
                color: #c9a24b;
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#overlayGrip {
                color: #64748b;
                font-size: 13px;
            }
            QLabel#overlayText {
                color: #e6edf3;
                font-size: 13px;
            }
            QPushButton#overlayClose {
                background: transparent;
                border: none;
                color: #8494a5;
                font-size: 15px;
                padding: 0;
            }
            QPushButton#overlayClose:hover {
                color: #f87171;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 7, 9, 9)
        root.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(6)

        grip = QLabel("≡")
        grip.setObjectName("overlayGrip")
        grip.setToolTip("按住窗口任意位置拖动")

        self.title_label = QLabel("译文")
        self.title_label.setObjectName("overlayTitle")

        self.close_btn = QPushButton("×")
        self.close_btn.setObjectName("overlayClose")
        self.close_btn.setToolTip("关闭（按 F11 呼出）")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self._on_close)

        top.addWidget(grip)
        top.addWidget(self.title_label)
        top.addStretch(1)
        top.addWidget(self.close_btn)
        root.addLayout(top)

        self.text_label = QLabel("")
        self.text_label.setObjectName("overlayText")
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        # 注意：不开启 TextSelectableByMouse —— 那会把鼠标事件吃掉，导致拖不动
        root.addWidget(self.text_label, 1)

    # ------------------------------------------------------------------
    # 显示 / 定位
    # ------------------------------------------------------------------
    def set_display_duration(self, seconds: int):
        self._display_duration = max(0, int(seconds))

    def show_result(self, text: str, detail: str = "", position: str | None = None):
        self._last_text = (text or "").strip()
        self._last_detail = (detail or "").strip()
        self.text_label.setText(self._last_text)
        self.title_label.setText(f"译文 · {self._last_detail}" if self._last_detail else "译文")
        if position:
            self._position = position

        # 先调尺寸（钳制最大宽高），再定位（钳制到屏幕内）——顺序很关键
        self.adjustSize()
        self._clamp_size()
        if not self._user_moved:
            self._apply_position()

        self.show()
        self.raise_()
        self._restart_auto_hide()

    def set_position(self, position: str):
        self._position = position
        self._user_moved = False

    def _clamp_size(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        max_w = max(MIN_WIDTH, int(geo.width() * MAX_WIDTH_RATIO))
        max_h = max(120, int(geo.height() * MAX_HEIGHT_RATIO))
        new_w = min(max(self.width(), MIN_WIDTH), max_w)
        new_h = min(self.height(), max_h)
        if new_w != self.width() or new_h != self.height():
            self.resize(new_w, new_h)

    def _apply_position(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        x, y = self.compute_position(
            self._position, self.width(), self.height(), screen.availableGeometry(), MARGIN
        )
        self.move(x, y)

    @staticmethod
    def compute_position(position: str, width: int, height: int, geo: QRect, margin: int = MARGIN):
        """按角落计算窗口左上角，并钳制在可用区域内（独立成函数便于单测）。"""
        x = geo.x() + margin
        y = geo.y() + margin

        if position in ("top-right", "bottom-right"):
            x = geo.x() + geo.width() - width - margin
        if position in ("bottom-left", "bottom-right"):
            y = geo.y() + geo.height() - height - margin

        min_x = geo.x() + margin
        min_y = geo.y() + margin
        max_x = geo.x() + geo.width() - width - margin
        max_y = geo.y() + geo.height() - height - margin

        # 窗口比屏幕还宽/高时，至少保证左上角落在屏幕内
        if max_x < min_x:
            max_x = min_x
        if max_y < min_y:
            max_y = min_y

        return (max(min_x, min(x, max_x)), max(min_y, min(y, max_y)))

    # ------------------------------------------------------------------
    # 自动隐藏
    # ------------------------------------------------------------------
    def _restart_auto_hide(self):
        self._auto_hide.stop()
        if self._display_duration > 0:
            self._auto_hide.start(self._display_duration * 1000)

    def enterEvent(self, event):
        if self._auto_hide.isActive():
            self._auto_hide.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.isVisible() and not self._penetrate:
            self._restart_auto_hide()
        super().leaveEvent(event)

    def hideEvent(self, event):
        self._auto_hide.stop()
        super().hideEvent(event)

    # ------------------------------------------------------------------
    # 鼠标穿透
    # ------------------------------------------------------------------
    def set_penetration(self, enabled: bool):
        self._penetrate = bool(enabled)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, self._penetrate)

    @property
    def penetrate(self) -> bool:
        return self._penetrate

    # ------------------------------------------------------------------
    # 拖动 / 双击 / 右键 / 键盘
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        # 优先交给系统处理（startSystemMove）：无边框 Tool 窗口压在游戏上层时，
        # 自己 move() 有时收不到稳定的 move 事件，表现为"拖不动"。
        handle = self.windowHandle()
        if handle is not None:
            try:
                if handle.startSystemMove():
                    self._drag_offset = None
                    self._user_moved = True
                    event.accept()
                    return
            except Exception:
                pass
        self._drag_offset = (
            event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        )
        event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            self._user_moved = True
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_close()

    def contextMenuEvent(self, event):
        menu = QMenu(self)

        copy_action = menu.addAction("复制译文")
        copy_action.triggered.connect(self._copy_text)

        penetrate_action = menu.addAction("鼠标穿透（点穿到游戏，F11 关闭）")
        penetrate_action.setCheckable(True)
        penetrate_action.setChecked(self._penetrate)
        penetrate_action.triggered.connect(self.set_penetration)

        menu.addSeparator()
        close_action = menu.addAction("关闭（F11 呼出）")
        close_action.triggered.connect(self._on_close)

        menu.exec(event.globalPos())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._on_close()
        else:
            super().keyPressEvent(event)

    def _copy_text(self):
        if not self._last_text:
            return
        try:
            import pyperclip

            pyperclip.copy(self._last_text)
        except Exception:
            pass

    def _on_close(self):
        self._auto_hide.stop()
        self.hide()
        self.closed.emit()

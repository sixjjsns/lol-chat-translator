"""译文悬浮窗：独立的置顶窗口，显示截图翻译结果，避免遮挡游戏界面。

特性：
- 无边框、置顶、半透明背景
- 可拖动、可关闭（Esc / 右键菜单）
- 可定位到屏幕四个角落
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)


class ResultOverlayWindow(QWidget):
    """译文悬浮窗口。"""

    closed = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self.setStyleSheet("""
            QWidget#overlayRoot {
                background-color: rgba(13, 21, 32, 230);
                border: 1px solid #c9a24b;
                border-radius: 10px;
            }
            QLabel#overlayTitle {
                color: #c9a24b;
                font-size: 12px;
                font-weight: 600;
            }
            QLabel#overlayText {
                color: #e6edf3;
                font-size: 14px;
            }
        """)

        self._build_ui()
        self._drag_offset = None

        self.resize(360, 180)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 12)
        root.setSpacing(6)

        # 标题栏
        self.title_label = QLabel("译文")
        self.title_label.setObjectName("overlayTitle")
        root.addWidget(self.title_label)

        # 译文内容
        self.text_label = QLabel("")
        self.text_label.setObjectName("overlayText")
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        root.addWidget(self.text_label, 1)

    # --- 显示译文 ---
    def show_result(self, text: str, detail: str = ""):
        self.text_label.setText(text)
        if detail:
            self.title_label.setText(f"译文 · {detail}")
        else:
            self.title_label.setText("译文")
        self.adjustSize()
        self.show()
        self.raise_()

    def set_position(self, position: str):
        """定位到屏幕角落：top-left / top-right / bottom-left / bottom-right。"""
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        margin = 24
        x = geo.left() + margin
        y = geo.top() + margin
        w = self.width()
        h = self.height()

        if position in ("top-right", "bottom-right"):
            x = geo.right() - w - margin
        if position in ("bottom-left", "bottom-right"):
            y = geo.bottom() - h - margin

        self.move(x, y)

    # --- 拖动 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_offset = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.hide()
            self.closed.emit()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        close_action = menu.addAction("关闭")
        close_action.triggered.connect(self._on_close)
        menu.exec(event.globalPos())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._on_close()

    def _on_close(self):
        self.hide()
        self.closed.emit()

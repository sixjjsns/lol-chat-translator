"""回复草稿悬浮窗:独立的置顶窗口,显示"你要发给队友的话"(F10 反向翻译结果)。

与阅读悬浮窗(result_overlay,显示"队友说了什么")严格区分:
- 本窗是可编辑的「草稿框」,翻译结果进来后你可手动改词,再点「复制」,
  切回游戏按 Ctrl+V 发出。
- 阅读悬浮窗是只读的,只用于"看懂队友消息",不能编辑、不能发送。

特性:
- 无边框、置顶、半透明背景
- 可拖动(按住窗口空白区域拖)
- 可关闭(Esc / 右键菜单 / 双击)
- 位置由设置页"悬浮窗位置"下拉框预选(不在悬浮窗上加按钮)
"""
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ReplyOverlayWindow(QWidget):
    """回复草稿悬浮窗口(F10 反向翻译结果)。"""

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

        # 用区别于阅读悬浮窗的配色(偏绿调),一眼区分"这是要发出去的草稿"
        self.setStyleSheet("""
            QWidget#replyRoot {
                background-color: rgba(16, 28, 20, 238);
                border: 1px solid #4caf7d;
                border-radius: 10px;
            }
            QLabel#replyTitle {
                color: #4caf7d;
                font-size: 12px;
                font-weight: 600;
            }
            QTextEdit#replyText {
                color: #e6f3ea;
                font-size: 14px;
                background-color: rgba(0, 0, 0, 40);
                border: 1px solid rgba(76, 175, 125, 90);
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton#copyBtn {
                color: #101c14;
                background-color: #4caf7d;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                padding: 6px 14px;
            }
            QPushButton#copyBtn:hover {
                background-color: #63c290;
            }
            QPushButton#copyBtn:pressed {
                background-color: #3d9165;
            }
        """)

        self._build_ui()
        self._drag_offset = None

        self.resize(420, 180)

    def _build_ui(self):
        self.setObjectName("replyRoot")

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 12)
        root.setSpacing(6)

        # 顶部:标题 + 复制按钮
        top = QHBoxLayout()
        top.setSpacing(8)

        self.title_label = QLabel("回复草稿")
        self.title_label.setObjectName("replyTitle")
        top.addWidget(self.title_label)
        top.addStretch(1)

        self.copy_btn = QPushButton("复制")
        self.copy_btn.setObjectName("copyBtn")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setToolTip("复制到剪贴板,然后切回游戏按 Ctrl+V 发出")
        self.copy_btn.clicked.connect(self._on_copy)
        top.addWidget(self.copy_btn)

        root.addLayout(top)

        # 草稿内容(可编辑)
        self.text_edit = QTextEdit("")
        self.text_edit.setObjectName("replyText")
        self.text_edit.setAcceptRichText(False)
        self.text_edit.setPlaceholderText("要发给队友的话…")
        root.addWidget(self.text_edit, 1)

    # --- 显示草稿 ---
    def show_result(self, text: str, detail: str = ""):
        self.text_edit.setPlainText(text or "")
        self.title_label.setText(f"回复草稿 · {detail}" if detail else "回复草稿")
        self.adjustSize()
        self.show()
        self.raise_()

    def set_position(self, position: str):
        """定位到屏幕角落:top-left/top-right/bottom-left/bottom-right。"""
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

    # --- 复制 ---
    def _on_copy(self):
        text = self.text_edit.toPlainText()
        if not text:
            return
        try:
            import pyperclip

            pyperclip.copy(text)
            self.copy_btn.setText("已复制")
            QTimer.singleShot(800, lambda: self.copy_btn.setText("复制"))
        except Exception:
            self.copy_btn.setText("复制失败")

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
        copy_action = menu.addAction("复制")
        copy_action.triggered.connect(self._on_copy)
        close_action = menu.addAction("关闭")
        close_action.triggered.connect(self._on_close)
        menu.exec(event.globalPos())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._on_close()

    def _on_close(self):
        self.hide()
        self.closed.emit()
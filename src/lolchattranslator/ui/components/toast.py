"""轻量提示条（Toast）：替代旧版“回复草稿悬浮窗”的非侵入式反馈。

为什么需要它
------------
v1.1.0 在 F10 之后会弹出一个**可编辑的绿色悬浮窗**，用来兜底复制。
但在游戏里它挡住画面、还要手动关，体验很差。v1.2.0 删掉了那个输入框，
改成 2.6 秒自动消失的只读提示条：

- 不接收鼠标（`WA_TransparentForMouseEvents`），绝不挡住游戏操作；
- 不抢焦点（`WA_ShowWithoutActivating`）；
- 只在屏幕底部中间一闪，告诉你“注入成功 / 已复制 / 失败原因”。

内容固定为“结果 + 下一步动作”，例如：
    ✅ 已注入游戏聊天框 · 按 Enter 发送
    📋 自动注入未开启，已复制 · 回游戏 Ctrl+V
"""

from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    Qt,
    QTimer,
)
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel

_STYLES = {
    "ok": ("#4ADE80", "rgba(18, 34, 24, 242)", "✅"),
    "info": ("#C9A24B", "rgba(30, 26, 16, 242)", "📋"),
    "error": ("#F87171", "rgba(38, 20, 22, 242)", "⚠️"),
}


class Toast(QFrame):
    """底部居中的一次性提示条。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._label = QLabel("", self)
        self._label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self._label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 20, 10)
        layout.setSpacing(10)
        layout.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)

        self._anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim.setDuration(260)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.hide()

    # ------------------------------------------------------------------
    def show_message(self, text: str, kind: str = "ok", duration_ms: int = 2600):
        """显示一条提示。kind: ok / info / error。"""
        color, bg, icon = _STYLES.get(kind, _STYLES["ok"])
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {color};
                border-radius: 12px;
            }}
            QLabel {{
                color: {color};
                font-family: "Microsoft YaHei UI";
                font-size: 13px;
                font-weight: 600;
            }}
            """
        )
        self._label.setText(f"{icon}  {text}")
        self.adjustSize()
        self._move_to_bottom_center()

        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

        self._timer.start(max(800, int(duration_ms)))

    def _move_to_bottom_center(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        area = screen.availableGeometry()
        x = area.left() + (area.width() - self.width()) // 2
        y = area.bottom() - self.height() - 96
        self.move(QPoint(x, y))

    def _fade_out(self):
        self._anim.stop()
        self._anim.setStartValue(self.windowOpacity())
        self._anim.setEndValue(0.0)
        try:
            self._anim.finished.disconnect()
        except (RuntimeError, TypeError):
            pass
        self._anim.finished.connect(self.hide)
        self._anim.start()

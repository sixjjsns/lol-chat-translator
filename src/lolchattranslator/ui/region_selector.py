"""屏幕区域选择器：全屏半透明遮罩 + 鼠标拖拽选择矩形区域。

非阻塞：通过 on_done 回调返回结果，不嵌套事件循环。
"""
from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget


class RegionSelector(QWidget):
    """全屏遮罩区域选择。"""

    regionSelected = Signal(dict)  # {'left','top','width','height'}
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self._start = None
        self._current = None
        self._selecting = False

        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

    # --- 鼠标事件 ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.position().toPoint()
            self._current = self._start
            self._selecting = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.cancelled.emit()
            self.close()

    def mouseMoveEvent(self, event):
        if self._selecting:
            self._current = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._selecting = False
            rect = self._selection_rect()
            self.close()
            if rect.width() > 5 and rect.height() > 5:
                self.regionSelected.emit({
                    "left": rect.x(),
                    "top": rect.y(),
                    "width": rect.width(),
                    "height": rect.height(),
                })
            else:
                self.cancelled.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()
            self.close()

    def _selection_rect(self) -> QRect:
        if self._start is None or self._current is None:
            return QRect()
        return QRect(self._start, self._current).normalized()

    def paintEvent(self, event):
        painter = QPainter(self)
        # 半透明遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
        if self._selecting and self._start is not None and self._current is not None:
            rect = self._selection_rect()
            # 选中区域挖空（恢复透明）
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            # 金色边框
            pen = QPen(QColor("#c9a24b"), 2)
            painter.setPen(pen)
            painter.drawRect(rect)

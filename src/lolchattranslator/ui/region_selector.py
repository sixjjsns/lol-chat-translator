"""屏幕区域选择器：全屏半透明遮罩 + 鼠标拖拽选择矩形区域。

非阻塞：通过 on_done 回调返回结果，不嵌套事件循环。
"""
from PySide6.QtCore import QPoint, QRect, Qt, Signal
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

        # 逻辑坐标 -> 物理坐标转换所需的屏幕信息。
        # Qt 的 event.position() 返回逻辑像素，而 mss 截图使用物理像素；
        # 在高 DPI 缩放（125%/150%）下必须按 devicePixelRatio 换算，否则框选与截图错位。
        self._screen = QApplication.primaryScreen()
        self._dpr = 1.0
        self._origin = QPoint(0, 0)
        if self._screen:
            self._dpr = float(self._screen.devicePixelRatio())
            self._origin = self._screen.geometry().topLeft()
            self.setGeometry(self._screen.geometry())
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
                self.regionSelected.emit(self._to_physical_region(rect))
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

    def _to_physical_region(self, rect: QRect) -> dict:
        """把 widget 局部逻辑坐标换算为 mss 所需的物理像素（虚拟桌面）坐标。

        Qt 的逻辑像素乘以 devicePixelRatio 得到物理像素；再加上屏幕在虚拟桌面
        中的逻辑原点，即可与 mss 的物理像素坐标对齐（含多显示器偏移）。
        """
        dpr = self._dpr
        left = round((self._origin.x() + rect.x()) * dpr)
        top = round((self._origin.y() + rect.y()) * dpr)
        width = round(rect.width() * dpr)
        height = round(rect.height() * dpr)
        return {
            "left": left,
            "top": top,
            "width": width,
            "height": height,
        }

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

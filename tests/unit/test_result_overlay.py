"""ResultOverlayWindow 行为测试：定位钳制、穿透、自动隐藏、拖拽可用性。

compute_position 是纯函数，直接测；其余需要 QApplication 的用例在无图形环境时自动跳过。
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

os.environ.setdefault("QT_QPA_PLATFORM", "windows")

from PySide6.QtCore import QRect  # noqa: E402

from lolchattranslator.ui.result_overlay import ResultOverlayWindow  # noqa: E402


class TestComputePosition(unittest.TestCase):
    """纯函数测试：不需要 QApplication。"""

    GEO = QRect(0, 0, 1920, 1040)  # 1080 屏减去任务栏

    def test_bottom_right_stays_inside(self):
        x, y = ResultOverlayWindow.compute_position("bottom-right", 400, 200, self.GEO)
        self.assertLessEqual(x + 400, self.GEO.width() - 16 + 1)
        self.assertLessEqual(y + 200, self.GEO.height() - 16 + 1)
        self.assertGreaterEqual(x, 16)
        self.assertGreaterEqual(y, 16)

    def test_all_corners_inside_for_normal_size(self):
        for corner in ("top-left", "top-right", "bottom-left", "bottom-right"):
            x, y = ResultOverlayWindow.compute_position(corner, 400, 200, self.GEO)
            self.assertGreaterEqual(x, 16)
            self.assertGreaterEqual(y, 16)
            self.assertLessEqual(x + 400, self.GEO.width() - 16 + 1)
            self.assertLessEqual(y + 200, self.GEO.height() - 16 + 1)

    def test_oversized_window_clamped_into_screen(self):
        # 窗口比屏幕还大：必须钳制，左上角至少落在屏幕内
        x, y = ResultOverlayWindow.compute_position("bottom-right", 4000, 3000, self.GEO)
        self.assertGreaterEqual(x, 16)
        self.assertGreaterEqual(y, 16)
        self.assertLessEqual(x, self.GEO.width())
        self.assertLessEqual(y, self.GEO.height())

    def test_corner_anchoring(self):
        # 右上角应该贴右边缘（正常尺寸下）
        x, y = ResultOverlayWindow.compute_position("top-right", 400, 200, self.GEO)
        self.assertAlmostEqual(x, self.GEO.width() - 400 - 16, delta=1)
        self.assertAlmostEqual(y, 16, delta=1)


class TestOverlayWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from PySide6.QtWidgets import QApplication

            cls.app = QApplication.instance() or QApplication([])
            cls._qt_ok = True
        except Exception:
            cls._qt_ok = False

    def setUp(self):
        if not self._qt_ok:
            self.skipTest("需要图形环境")
        self.overlay = ResultOverlayWindow(display_duration=15)

    def test_show_result_stores_last_text(self):
        self.overlay.show_result("对面打野在下", "1.8s", "bottom-right")
        self.assertEqual(self.overlay._last_text, "对面打野在下")
        self.assertEqual(self.overlay._last_detail, "1.8s")

    def test_auto_hide_timer_starts_when_duration_positive(self):
        self.overlay.set_display_duration(15)
        self.overlay.show_result("hello", "", "bottom-right")
        self.assertTrue(self.overlay._auto_hide.isActive())

    def test_auto_hide_disabled_when_zero(self):
        self.overlay.set_display_duration(0)
        self.overlay.show_result("hello", "", "bottom-right")
        self.assertFalse(self.overlay._auto_hide.isActive())

    def test_penetration_toggles_mouse_transparency(self):
        self.overlay.set_penetration(True)
        self.assertTrue(
            self.overlay.testAttribute(
                __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.WidgetAttribute.WA_TransparentForMouseEvents
            )
        )
        self.overlay.set_penetration(False)
        self.assertFalse(self.overlay.penetrate)

    def test_text_label_does_not_swallow_mouse(self):
        # v1.2.1 修复点：正文不允许鼠标选择，事件应穿透到窗口本体（可拖动）
        from PySide6.QtCore import Qt

        flags = self.overlay.text_label.textInteractionFlags()
        self.assertNotIn(Qt.TextInteractionFlag.TextSelectableByMouse, flags)
        self.assertNotIn(Qt.TextInteractionFlag.TextSelectableByKeyboard, flags)


if __name__ == "__main__":
    unittest.main()

"""RegionSelector DPI 坐标换算测试（纯逻辑，不依赖 QApplication 实例）。"""

from PySide6.QtCore import QPoint, QRect

from lolchattranslator.ui.region_selector import RegionSelector


def _make_selector(dpr: float, origin: tuple = (0, 0)) -> RegionSelector:
    """构造一个不初始化 QWidget 的最小对象，仅设置换算所需属性。"""
    sel = RegionSelector.__new__(RegionSelector)
    sel._dpr = float(dpr)
    sel._origin = QPoint(*origin)
    return sel


def test_dpr_1_identity():
    sel = _make_selector(1.0)
    result = sel._to_physical_region(QRect(100, 50, 200, 100))
    assert result == {"left": 100, "top": 50, "width": 200, "height": 100}


def test_dpr_2_scales_all_fields():
    sel = _make_selector(2.0)
    result = sel._to_physical_region(QRect(100, 50, 200, 100))
    assert result == {"left": 200, "top": 100, "width": 400, "height": 200}


def test_dpr_1_5_rounding():
    sel = _make_selector(1.5)
    result = sel._to_physical_region(QRect(100, 20, 30, 40))
    assert result == {"left": 150, "top": 30, "width": 45, "height": 60}


def test_multi_monitor_origin_offset():
    # 副屏在虚拟桌面中的逻辑原点偏移（如左侧 1920 宽的副屏）
    sel = _make_selector(1.5, origin=(-1920, 0))
    result = sel._to_physical_region(QRect(10, 20, 30, 40))
    assert result == {"left": round((-1920 + 10) * 1.5), "top": 30, "width": 45, "height": 60}


def test_origin_not_applied_to_size():
    # 宽高是局部尺寸，不应叠加原点
    sel = _make_selector(2.0, origin=(500, 300))
    result = sel._to_physical_region(QRect(10, 20, 30, 40))
    assert result == {"left": 1020, "top": 640, "width": 60, "height": 80}

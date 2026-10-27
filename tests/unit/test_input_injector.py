"""InputInjector 单元测试：代理对拆解 / ctypes 结构体布局 / 平台守卫 / 主流程。

注意：本测试只验证纯逻辑与 ctypes 结构体布局，**不实际调用 SendInput**，
避免向真实窗口注入按键。
"""

import ctypes
from ctypes import wintypes
from unittest import mock

import pytest

from lolchattranslator.services import input_injector
from lolchattranslator.services.input_injector import InputInjector


# ---------------------------------------------------------------------------
# UTF-16 码元拆解
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "char, expected",
    [
        ("A", (0x41,)),                    # ASCII（BMP）
        ("中", (0x4E2D,)),                 # 中文 BMP 字符 U+4E2D -> 单个码元
        ("😀", (0xD83D, 0xDE00)),          # 增补平面 emoji U+1F600 -> 高低代理对
        ("𝄞", (0xD834, 0xDD1E)),          # 增补平面 U+1D11E -> 高低代理对
    ],
)
def test_code_units(char, expected):
    assert InputInjector._code_units(char) == expected


def test_code_units_type_is_tuple_of_int():
    units = InputInjector._code_units("😀")
    assert isinstance(units, tuple)
    assert all(isinstance(u, int) for u in units)


# ---------------------------------------------------------------------------
# ctypes 结构体定义正确性（Windows SDK WinUser.h）
# ---------------------------------------------------------------------------
def test_sendinput_constants():
    assert input_injector.INPUT_KEYBOARD == 0x0001
    assert input_injector.KEYEVENTF_KEYUP == 0x0002
    assert input_injector.KEYEVENTF_UNICODE == 0x0004


@pytest.mark.skipif(ctypes.sizeof(ctypes.c_size_t) != 8, reason="仅 x64 验证布局")
def test_keybdinput_field_layout():
    kb = input_injector._KeybdInput
    assert ctypes.sizeof(kb) == 24
    assert kb.wVk.offset == 0
    assert kb.wScan.offset == 2
    assert kb.dwFlags.offset == 4
    assert kb.time.offset == 8
    # ULONG_PTR 需 8 字节对齐，offset 应为 16
    assert kb.dwExtraInfo.offset == 16


def _reference_input_size() -> int:
    """按 Windows SDK 完整定义（MOUSEINPUT + KEYBDINPUT + HARDWAREINPUT）计算 INPUT 大小。"""

    class _MouseInput(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_size_t),
        ]

    class _HardwareInput(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class _RefUnion(ctypes.Union):
        _fields_ = [
            ("mi", _MouseInput),
            ("ki", input_injector._KeybdInput),
            ("hi", _HardwareInput),
        ]

    class _RefInput(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", _RefUnion)]

    return ctypes.sizeof(_RefInput)


@pytest.mark.skipif(ctypes.sizeof(ctypes.c_size_t) != 8, reason="仅 x64 验证大小")
def test_input_struct_size_matches_windows_sdk():
    """INPUT 结构体必须与 Windows SDK 的 sizeof(INPUT) 一致，否则 SendInput 的 cbSize 校验失败。

    x64 下 Windows SDK 的 sizeof(INPUT) == 40（union 按最大成员 MOUSEINPUT=32 对齐），
    而非只含 KEYBDINPUT 分支时的 32。
    """
    ref = _reference_input_size()
    assert ref == 40  # 先锁定参考实现的正确性
    assert ctypes.sizeof(input_injector._Input) == ref


# ---------------------------------------------------------------------------
# 非 Windows 平台守卫
# ---------------------------------------------------------------------------
def test_inject_text_empty_returns_zero():
    assert InputInjector().inject_text("") == 0


def test_inject_text_non_windows_returns_zero_without_loading_dll():
    inj = InputInjector()
    with mock.patch("lolchattranslator.services.input_injector.sys.platform", "linux"):
        with mock.patch.object(inj, "_ensure_loaded") as ensure:
            assert inj.inject_text("hello") == 0
            ensure.assert_not_called()


# ---------------------------------------------------------------------------
# inject_text 主流程（mock 掉 Win32 与 sleep，验证逐字符注入、不自动 Enter）
# ---------------------------------------------------------------------------
def test_inject_text_injects_each_code_unit_in_order():
    inj = InputInjector()
    with mock.patch.object(inj, "_ensure_loaded"), \
            mock.patch.object(inj, "_focus_game_window"), \
            mock.patch.object(inj, "_inject_code_unit", return_value=True) as unit, \
            mock.patch("lolchattranslator.services.input_injector.time.sleep"):
        count = inj.inject_text("A中😀", delay_ms=0)

    # 'A'(1) + '中'(1) + '😀'(2) = 4 个 UTF-16 码元
    assert count == 4
    injected_units = [call.args[0] for call in unit.call_args_list]
    assert injected_units == [0x41, 0x4E2D, 0xD83D, 0xDE00]


def test_inject_text_stops_on_first_failure():
    inj = InputInjector()
    with mock.patch.object(inj, "_ensure_loaded"), \
            mock.patch.object(inj, "_focus_game_window"), \
            mock.patch.object(inj, "_inject_code_unit", side_effect=[False]) as unit, \
            mock.patch("lolchattranslator.services.input_injector.time.sleep"):
        count = inj.inject_text("AB", delay_ms=0)

    assert count == 0
    assert unit.call_count == 1


def test_inject_text_negative_delay_is_clamped():
    inj = InputInjector()
    with mock.patch.object(inj, "_ensure_loaded"), \
            mock.patch.object(inj, "_focus_game_window"), \
            mock.patch.object(inj, "_inject_code_unit", return_value=True) as unit, \
            mock.patch("lolchattranslator.services.input_injector.time.sleep"):
        inj.inject_text("A", delay_ms=-5)
    # delay_ms 为负时应被钳制为 0，仍正常注入
    assert unit.call_args_list[0].args[1] == 0.0

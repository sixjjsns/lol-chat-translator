"""游戏聊天框文本注入服务（Windows / 高风险功能）。

**警告（WARNING）**
向游戏窗口自动注入按键可能违反 Riot 服务条款，存在账号封禁风险。
本模块默认不启用，用户必须在设置页显式勾选「自动粘贴」后才会被调用。

原理
----
LoL 国际服会屏蔽从游戏外部粘贴内容到聊天框（Ctrl+V 失效）。本模块改用
Windows ``SendInput`` + ``KEYEVENTF_UNICODE`` 逐字符注入 Unicode 码点：
每个字符构造一个 ``KEYBDINPUT``，其中 ``wVk=0``、
``wScan=字符 UTF-16 码元``、``dwFlags=KEYEVENTF_UNICODE``（按下）/
``KEYEVENTF_UNICODE|KEYEVENTF_KEYUP``（抬起）。

这样可绕过 IME 输入法与剪贴板，直接注入中文/英文/日文/韩文/emoji。

设计约束
--------
- 只注入文本，**绝不自动按 Enter 发送**，由用户确认后手动发送。
- 注入前尝试聚焦 LoL 客户端窗口；找不到则回退到当前前台窗口。
- 使用 ctypes 实现 ``SendInput``，避免依赖 pywin32 的封装差异。
- 仅在 Windows 上可用，其他平台直接跳过并记录 warning。
"""

from __future__ import annotations

import ctypes
import random
import sys
import time
from ctypes import wintypes

from ..infrastructure.logging_config import get_logger

logger = get_logger()

# SendInput 相关常量（Windows SDK WinUser.h）
INPUT_KEYBOARD = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

# 64 位安全：ULONG_PTR 在 32/64 位下长度自适应
ULONG_PTR = ctypes.c_size_t

# LoL 客户端/游戏窗口可能的标题与窗口类名（按优先级尝试）
_GAME_WINDOW_TITLES = (
    "League of Legends",
    "League of Legends (TM) Client",
    "LoL",
)
_GAME_WINDOW_CLASS = "RiotWindowClass"

# 行为伪装（降低被反作弊启发式判定命中的概率）：
# 真人打字每字符间隔并非恒定，这里在 base 附近做随机抖动，避免"匀速注入"特征。
_DELAY_JITTER_RATIO = 0.5  # 抖动幅度 ±50%


class _KeybdInput(ctypes.Structure):
    """KEYBDINPUT 结构体（WinUser.h）。"""

    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _MouseInput(ctypes.Structure):
    """MOUSEINPUT 结构体（WinUser.h）。"""

    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _HardwareInput(ctypes.Structure):
    """HARDWAREINPUT 结构体（WinUser.h）。"""

    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]


class _InputUnion(ctypes.Union):
    """INPUT 结构体内的联合体，必须包含全部分支以保证 sizeof 与 SDK 一致。

    联合体大小为三个分支的最大值（x64：MOUSEINPUT 32B / KEYBDINPUT 24B /
    HARDWAREINPUT 8B），加上前面的 type 字段与对齐填充后，sizeof(INPUT) 应为 40B。
    SendInput 会严格校验 cbSize，缺失分支会导致结构体偏小而被拒绝。
    """

    _fields_ = [
        ("mi", _MouseInput),
        ("ki", _KeybdInput),
        ("hi", _HardwareInput),
    ]


class _Input(ctypes.Structure):
    """INPUT 结构体（WinUser.h）。"""

    _anonymous_ = ("i",)
    _fields_ = [("type", wintypes.DWORD), ("i", _InputUnion)]


class InputInjector:
    """用 SendInput 将文本逐字符注入游戏窗口。"""

    def __init__(self) -> None:
        self._user32 = None
        self._kernel32 = None
        self._send_input = None

    # ------------------------------------------------------------------
    # 对外接口
    # ------------------------------------------------------------------
    def inject_text(self, text: str, delay_ms: float = 10.0) -> int:
        """把 ``text`` 逐字符注入当前游戏窗口，返回注入的 UTF-16 码元数量。

        Args:
            text: 要注入的文本（支持任意 Unicode，含 emoji 增补平面字符）。
            delay_ms: 每个码元按下/抬起之间的间隔（毫秒）。默认 10ms，
                过小可能被游戏吞字，过大则注入变慢。

        Returns:
            成功注入的 UTF-16 码元数量；非 Windows 平台或文本为空时返回 0。

        Note:
            本方法不会自动发送 Enter，由用户确认后手动发送。
        """
        if not text:
            return 0
        if sys.platform != "win32":
            logger.warning("输入注入仅支持 Windows，已跳过自动粘贴")
            return 0
        if delay_ms < 0:
            delay_ms = 0.0

        self._ensure_loaded()
        logger.warning(
            "自动粘贴：准备向游戏聊天框注入 %d 个字符（高风险功能）", len(text)
        )

        hwnd = self._focus_game_window()
        if not hwnd:
            logger.warning("自动粘贴：焦点不在游戏窗口，放弃注入（请先点击游戏聊天框）")
            return 0
        time.sleep(delay_ms / 1000.0)

        injected = 0
        failed = False
        for char in text:
            for code_unit in self._code_units(char):
                if self._inject_code_unit(code_unit, delay_ms):
                    injected += 1
                else:
                    logger.warning("自动粘贴：注入字符 %r 失败，停止注入", char)
                    failed = True
                    break
            if failed:
                break

        time.sleep(delay_ms / 1000.0)
        logger.warning("自动粘贴：注入完成，共 %d 个 UTF-16 码元", injected)
        return injected

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------
    def _ensure_loaded(self) -> None:
        """惰性加载 user32/kernel32 并声明 Win32 函数签名（避免句柄截断）。"""
        if self._user32 is not None:
            return
        self._user32 = ctypes.windll.user32
        self._kernel32 = ctypes.windll.kernel32

        self._send_input = self._user32.SendInput
        self._send_input.argtypes = (
            wintypes.UINT,
            ctypes.POINTER(_Input),
            ctypes.c_int,
        )
        self._send_input.restype = wintypes.UINT

        self._user32.FindWindowW.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR)
        self._user32.FindWindowW.restype = wintypes.HWND
        self._user32.GetForegroundWindow.argtypes = ()
        self._user32.GetForegroundWindow.restype = wintypes.HWND
        self._user32.SetForegroundWindow.argtypes = (wintypes.HWND,)
        self._user32.SetForegroundWindow.restype = wintypes.BOOL
        self._user32.BringWindowToTop.argtypes = (wintypes.HWND,)
        self._user32.BringWindowToTop.restype = wintypes.BOOL
        self._user32.IsIconic.argtypes = (wintypes.HWND,)
        self._user32.IsIconic.restype = wintypes.BOOL
        self._user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)
        self._user32.ShowWindow.restype = wintypes.BOOL
        self._user32.GetWindowThreadProcessId.argtypes = (
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        )
        self._user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        self._user32.AttachThreadInput.argtypes = (
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.BOOL,
        )
        self._user32.AttachThreadInput.restype = wintypes.BOOL
        self._user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
        self._user32.GetWindowTextLengthW.restype = ctypes.c_int
        self._user32.GetWindowTextW.argtypes = (
            wintypes.HWND,
            wintypes.LPWSTR,
            ctypes.c_int,
        )
        self._user32.GetWindowTextW.restype = ctypes.c_int
        self._kernel32.GetCurrentThreadId.argtypes = ()
        self._kernel32.GetCurrentThreadId.restype = wintypes.DWORD

    @staticmethod
    def _code_units(char: str) -> tuple[int, ...]:
        """把一个 Unicode 字符拆成 UTF-16 码元（BMP 1 个，增补平面 2 个）。"""
        codepoint = ord(char)
        if codepoint <= 0xFFFF:
            return (codepoint,)
        # 增补平面字符（如 emoji）-> 高/低代理对
        codepoint -= 0x10000
        high = 0xD800 | (codepoint >> 10)
        low = 0xDC00 | (codepoint & 0x3FF)
        return (high, low)

    def _find_game_window(self) -> int:
        """按标题/类名查找 LoL 窗口，返回 HWND；找不到返回 0。"""
        for title in _GAME_WINDOW_TITLES:
            hwnd = self._user32.FindWindowW(None, title)
            if hwnd:
                logger.info("自动粘贴：找到游戏窗口 '%s' (hwnd=%d)", title, hwnd)
                return hwnd
        hwnd = self._user32.FindWindowW(_GAME_WINDOW_CLASS, None)
        if hwnd:
            logger.info("自动粘贴：按窗口类名找到游戏窗口 (hwnd=%d)", hwnd)
        return hwnd or 0

    def _focus_game_window(self) -> int:
        """聚焦游戏窗口并返回其 HWND（找不到则返回 0）。

        上一版的问题：改成"仅检测前台、不抢焦点"后，F10 触发时焦点必然在
        本工具窗口而非游戏，导致每次都在注入前 `return 0` 放弃，一次都没真正
        注入过。这里改回"主动抢焦点"：翻译完成后把游戏窗口拉回前台再注入，
        这样 KEYEVENTF_UNICODE 才有机会被游戏接收。

        说明：仍无法替用户在游戏内部点开聊天输入框，需要用户先手动在游戏里
        按 Enter（或 /）进入输入状态，本方法只负责把窗口带回前台并注入文本。
        """
        # 1) 若前台窗口已经是游戏，直接用
        fg = self._user32.GetForegroundWindow()
        if fg and self._is_game_window(fg):
            logger.info("自动粘贴：前台窗口即游戏窗口 (hwnd=%d)，直接注入", fg)
            return fg

        # 2) 否则查找游戏窗口并主动抢焦点
        game = self._find_game_window()
        if not game:
            logger.warning("自动粘贴：未找到 LoL 游戏窗口，注入将失败")
            return 0

        logger.info("自动粘贴：主动聚焦游戏窗口 (hwnd=%d) 后注入", game)

        # SetForegroundWindow 受系统限制，需先 AttachThreadInput 提高成功率
        fg_thread = self._user32.GetWindowThreadProcessId(fg, None) if fg else 0
        game_thread = self._user32.GetWindowThreadProcessId(game, None)
        cur_thread = self._kernel32.GetCurrentThreadId()
        attached = False
        if fg_thread and game_thread:
            self._user32.AttachThreadInput(cur_thread, fg_thread, True)
            self._user32.AttachThreadInput(cur_thread, game_thread, True)
            attached = True

        # 最小化则先还原
        if self._user32.IsIconic(game):
            self._user32.ShowWindow(game, 9)  # SW_RESTORE
        self._user32.SetForegroundWindow(game)
        self._user32.BringWindowToTop(game)

        if attached:
            self._user32.AttachThreadInput(cur_thread, fg_thread, False)
            self._user32.AttachThreadInput(cur_thread, game_thread, False)

        # 给系统一点时间完成前台切换
        time.sleep(0.15)
        return game

    def _is_game_window(self, hwnd: int) -> bool:
        """判断 hwnd 是否为 LoL 游戏/客户端窗口（按标题前缀或类名）。"""
        # 类名匹配
        if self._user32.FindWindowW(_GAME_WINDOW_CLASS, None) == hwnd:
            return True
        # 标题匹配（获取窗口标题）
        length = self._user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return False
        buf = ctypes.create_unicode_buffer(length + 1)
        self._user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value
        for prefix in _GAME_WINDOW_TITLES:
            if title.startswith(prefix):
                return True
        return False

    def _inject_code_unit(self, code_unit: int, delay_ms: float) -> bool:
        """注入单个 UTF-16 码元（按下 + 抬起），返回是否成功。

        每字符间隔做 ±50% 随机抖动，模拟真人打字节奏，避免匀速注入特征。
        """
        for flags in (KEYEVENTF_UNICODE, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP):
            inp = _Input()
            inp.type = INPUT_KEYBOARD
            inp.ki.wVk = 0
            inp.ki.wScan = code_unit
            inp.ki.dwFlags = flags
            inp.ki.time = 0
            inp.ki.dwExtraInfo = 0
            sent = self._send_input(1, ctypes.byref(inp), ctypes.sizeof(_Input))
            if sent != 1:
                logger.warning(
                    "自动粘贴：SendInput 失败 code_unit=0x%04X，返回值=%d",
                    code_unit,
                    sent,
                )
                return False
            if delay_ms > 0:
                # 随机抖动：base * (1 ± 0.5)
                jittered = delay_ms * random.uniform(
                    1 - _DELAY_JITTER_RATIO, 1 + _DELAY_JITTER_RATIO
                )
                time.sleep(jittered / 1000.0)
        return True

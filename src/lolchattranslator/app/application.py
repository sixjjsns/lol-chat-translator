"""应用核心：Application 类，编排 UI、翻译服务、快捷键、托盘、任务管理。

架构（Qt 信号槽）：
- 主线程：QApplication + MainWindow，所有 Qt 操作都在主线程。
- keyboard 线程：全局快捷键回调，通过 Qt 信号安全回传主线程。
- pystray 线程：托盘菜单回调，同样通过信号回传。
- TaskManager（QThread）：翻译任务在 worker 线程执行，结果通过信号回传。

v1.2.0 交互变更
---------------
- **删除游戏内 F10 输入悬浮窗**（ReplyOverlayWindow）：它挡画面、还要手动关。
- F10 的链路变成：主窗口输入中文 → 翻译 → 直接注入游戏聊天框（核心注入逻辑不变）
  → 底部 Toast 提示 2.6 秒自动消失。
- 注入未开启或失败时自动复制到剪贴板，Toast 提示“回游戏 Ctrl+V”。
- F6 的只读阅读悬浮窗保留（不挡输入，只是看译文）。
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from ..core.models import TaskKind, TranslationRequest, TranslationResult
from ..core.translation_service import TranslationService
from ..infrastructure.config_store import ConfigStore
from ..infrastructure.logging_config import get_logger, setup_logging
from ..infrastructure.secret_store import SecretStore
from ..providers import available_providers
from ..services.hotkey_service import DEFAULT_HOTKEYS, HotkeyManager
from ..services.screenshot_service import ScreenshotService
from ..services.tray_service import TrayService
from ..ui.components.toast import Toast
from ..ui.main_window import MainWindow
from ..ui.region_selector import RegionSelector
from ..ui.result_overlay import ResultOverlayWindow
from .task_manager import TaskManager

logger = get_logger()


class _Bridge(QObject):
    """跨线程信号桥：把后台线程（keyboard/pystray）的动作安全投递到主线程。

    keyboard 库的全局钩子回调运行在独立线程，pystray 菜单回调同样如此。
    这些线程不能直接操作 Qt 控件，否则会死锁/白屏。这里用一个 Qt 信号，
    emit 后会自动跨线程排队到主线程执行槽函数。
    """

    actionTriggered = Signal(str)


class Application(QObject):
    """应用主控制器。"""

    def __init__(self, qapp: QApplication):
        super().__init__()
        self.qapp = qapp
        self.config = ConfigStore()
        self.secret_store = SecretStore()
        self.translation_service = TranslationService(self.config)
        self.screenshot = ScreenshotService()
        self.hotkeys = HotkeyManager()

        self._naturalness = 0.7  # temperature
        self._last_png = None
        self._selecting = False
        self._closing = False
        self._tray = None

        # 跨线程动作桥（keyboard/pystray -> 主线程）
        self._bridge = _Bridge()
        self._bridge.actionTriggered.connect(self._handle_action)

        # 任务管理器（worker 线程）
        self.task_manager = TaskManager(self.translation_service)

        # 主窗口
        providers = self._load_providers_meta()
        self.window = MainWindow(providers, self.config, self.secret_store.get_key())

        # 译文阅读悬浮窗（F6 截图翻译结果，只读）
        self.overlay = ResultOverlayWindow()

        # 轻量提示条（替代旧的回复草稿悬浮窗）
        self.toast = Toast()

        self._connect_signals()

    # ================= 初始化辅助 =================
    def _load_providers_meta(self) -> dict:
        """从配置读取 providers 元信息。"""
        meta = self.config.get("providers", {})
        result = {}
        for key in available_providers():
            if key == "openai_compat":
                continue
            if key in meta:
                result[key] = meta[key]
            else:
                result[key] = {"name": key, "base_url": "", "model": "", "needs_key": True}
        return result

    def _connect_signals(self):
        w = self.window
        w.captureRequested.connect(self.capture_translate)
        w.selectRegionRequested.connect(self.select_region)
        w.retranslateRequested.connect(self.retranslate)
        w.copyRequested.connect(self.copy_last)
        w.replyRequested.connect(self.send_reply)
        w.naturalnessChanged.connect(self._on_naturalness_change)
        w.saveSettingsRequested.connect(self._save_settings)
        w.testConnectionRequested.connect(self.test_connection)
        w.clearKeyRequested.connect(self._clear_key)
        self.task_manager.finished.connect(self._on_task_finished)
        self.task_manager.failed.connect(self._on_task_failed)

    # ================= 启动 / 退出 =================
    def run(self):
        setup_logging()
        # 应用已保存的界面语言
        self.window.apply_language(self.config.get("language.ui", "zh"))
        self._refresh_ui_state()
        self.window.show()

        # 首次启动引导
        if not self.secret_store.has_key() or not self.config.get("capture.region"):
            self.window.show_settings()

        self._register_hotkeys()
        self.task_manager.start()
        self._start_tray()

    def _refresh_ui_state(self):
        """把配置状态同步到界面上的状态胶囊。"""
        provider = self.config.get("api.provider", "deepseek")
        meta = self._load_providers_meta().get(provider, {})
        self.window.set_provider_text(meta.get("name", provider))
        self.window.set_auto_paste_state(bool(self.config.get("paste.auto_paste", False)))
        self.window.set_region_state(bool(self.config.get("capture.region")))
        self.window.set_hotkey_labels(self.config.get("hotkeys", DEFAULT_HOTKEYS))

    def shutdown(self):
        if self._closing:
            return
        self._closing = True
        logger.info("正在退出...")
        self.hotkeys.unregister_all()
        self.task_manager.stop()
        if self._tray:
            self._tray.stop()
        self.qapp.quit()

    # ================= 快捷键 / 托盘 =================
    def _post_action(self, action: str):
        """从后台线程投递动作到主线程（线程安全）。"""
        self._bridge.actionTriggered.emit(action)

    def _handle_action(self, action: str):
        """主线程执行动作（由 bridge 信号驱动）。"""
        try:
            if action == "capture_translate":
                self.capture_translate()
            elif action == "retranslate":
                self.retranslate()
            elif action == "copy_last":
                self.copy_last()
            elif action == "toggle_window":
                self.toggle_window()
            elif action == "select_region":
                self.select_region()
            elif action == "reply_translate":
                self.reply_translate()
            elif action == "cancel":
                self.cancel_current()
            elif action == "test_connection":
                self.test_connection()
            elif action == "open_log":
                self.open_log_dir()
            elif action == "show_settings":
                self.window.show_settings()
            elif action == "quit":
                self.shutdown()
        except Exception as e:
            logger.warning("处理动作异常: %s", e)

    def _register_hotkeys(self):
        try:
            mapping = self.config.get("hotkeys", DEFAULT_HOTKEYS) or DEFAULT_HOTKEYS
            handlers = {
                "capture_translate": lambda: self._post_action("capture_translate"),
                "retranslate": lambda: self._post_action("retranslate"),
                "copy_last": lambda: self._post_action("copy_last"),
                "toggle_window": lambda: self._post_action("toggle_window"),
                "select_region": lambda: self._post_action("select_region"),
                "reply_translate": lambda: self._post_action("reply_translate"),
                "cancel": lambda: self._post_action("cancel"),
            }
            # 只注册有 handler 的动作，自动清理历史残留（如已废弃的 toggle_overlay）
            mapping = {action: key for action, key in mapping.items() if action in handlers}
            warnings = self.hotkeys.register_all(mapping, handlers)
            for warn in warnings:
                logger.warning(warn)
            self.window.set_hotkey_labels(mapping)
        except Exception as e:
            logger.warning("快捷键注册失败: %s", e)

    def _start_tray(self):
        try:
            actions = {
                "显示/隐藏主窗口": lambda: self._post_action("toggle_window"),
                "截取翻译": lambda: self._post_action("capture_translate"),
                "选择聊天区域": lambda: self._post_action("select_region"),
                "测试 API 连接": lambda: self._post_action("test_connection"),
                "设置": lambda: self._post_action("show_settings"),
                "打开日志目录": lambda: self._post_action("open_log"),
            }
            self._tray = TrayService(
                menu_actions=actions,
                on_quit=lambda: self._post_action("quit"),
            )
            self._tray.start()
        except Exception as e:
            logger.warning("托盘启动失败: %s", e)
            self._tray = None

    # ================= 截图翻译 =================
    def capture_translate(self):
        if self.task_manager.busy:
            logger.info("已有请求进行中，忽略")
            return
        region = self.config.get("capture.region")
        if not region:
            self.window.set_status("还没有设置聊天区域 · 请先在游戏里按 F9 框选聊天框")
            self.toast.show_message("请先框选聊天区域（F9）", "error")
            self.select_region()
            return
        try:
            png = self.screenshot.capture_region(region)
        except Exception as e:
            self.window.show_error(str(e))
            return
        self._last_png = png
        self.window.set_busy(True)
        self.window.set_status("识别中…")
        req = TranslationRequest(
            kind=TaskKind.IMAGE,
            image_bytes=png,
            target_lang=self.config.get("language.target", "zh"),
            source_lang=self.config.get("language.source", "auto"),
            temperature=self._naturalness,
        )
        self.task_manager.enqueue(req)

    def retranslate(self):
        if self.task_manager.busy:
            return
        if self._last_png is None:
            self.window.set_status("暂无最近截图，请先按 F6")
            return
        self.window.set_busy(True)
        self.window.set_status("重新识别中…")
        req = TranslationRequest(
            kind=TaskKind.IMAGE,
            image_bytes=self._last_png,
            target_lang=self.config.get("language.target", "zh"),
            source_lang=self.config.get("language.source", "auto"),
            temperature=self._naturalness,
            force=True,
        )
        self.task_manager.enqueue(req)

    # ================= 反向翻译 =================
    def send_reply(self, text: str, target_lang: str):
        req = TranslationRequest(
            kind=TaskKind.REPLY,
            text=text,
            target_lang=target_lang,
            temperature=self._naturalness,
        )
        self.window.set_busy(True)
        self.window.set_status("翻译回复中…")
        self.task_manager.enqueue(req)

    def reply_translate(self):
        """快捷键触发：读取主窗口输入框内容，翻译并注入。"""
        text = self.window.translation_page.get_reply_text()
        if not text:
            self.window.set_status("输入框为空，请先在主窗口输入要发的话")
            self.toast.show_message("先在主窗口输入中文，再按 F10", "info")
            return
        target = self.window.translation_page.get_target_lang()
        self.send_reply(text, target)

    # ================= 结果回传 =================
    def _on_task_finished(self, result: TranslationResult):
        self.window.set_busy(False)

        if result.kind == TaskKind.REPLY:
            self._handle_reply_result(result)
            return

        detail = f"{result.total_ms:.0f}ms" + (" (缓存)" if result.cached else "")
        self.window.set_duration(detail)
        if result.ok and (result.translated or "").strip():
            self.window.set_result(result.translated)
            self.window.set_status(f"翻译完成 · {detail}")
            self._show_overlay_result(result.translated, detail)
        elif result.ok:
            logger.warning("截图翻译返回空内容，可能截图无聊天文字或模型未识别")
            self.window.set_status("翻译完成，但未识别到内容 · " + detail)
            self._show_overlay_result("（未识别到聊天内容，请确认截图区域包含聊天框）", detail)
        else:
            self.window.show_error(f"翻译失败: {result.error}")
            self.toast.show_message(f"翻译失败：{result.error}", "error")

    def _handle_reply_result(self, result: TranslationResult):
        """反向翻译结果：注入 / 复制 + Toast 提示（不再弹游戏内输入框）。"""
        text = (result.translated or "").strip()
        self.window.set_reply_result(text)
        detail = f"{result.total_ms:.0f}ms" + (" (缓存)" if result.cached else "")

        if not text:
            self.window.set_status("回复翻译完成，但内容为空 · " + detail)
            self.toast.show_message("未识别到内容，请重试", "error")
            return

        injected = 0
        if self.config.get("paste.auto_paste", False):
            try:
                from ..services.input_injector import InputInjector

                delay_ms = float(self.config.get("paste.delay_ms", 10))
                logger.warning("自动注入已启用，正在向游戏聊天框注入译文（高风险功能）")
                injected = InputInjector().inject_text(text, delay_ms=delay_ms)
            except Exception as e:
                logger.warning("自动注入异常: %s", e)
                injected = 0

        if injected <= 0:
            self._copy_to_clipboard(text)
            self.window.set_status(f"已复制译文 · 回游戏按 Ctrl+V 发送（{detail}）")
            self.toast.show_message("已复制 · 回游戏按 Ctrl+V", "info")
        else:
            self.window.set_status(f"已注入游戏聊天框 · 按 Enter 发送（{detail}）")
            self.toast.show_message("已注入游戏聊天框 · 按 Enter 发送", "ok")

    @staticmethod
    def _copy_to_clipboard(text: str) -> bool:
        try:
            import pyperclip

            pyperclip.copy(text)
            return True
        except Exception as e:
            logger.warning("复制到剪贴板失败: %s", e)
            return False

    def _show_overlay_result(self, text: str, detail: str = ""):
        """译文显示到「阅读」悬浮窗，并按配置定位。"""
        position = self.config.get("overlay.position", "bottom-right")
        self.overlay.set_position(position)
        self.overlay.show_result(text, detail)

    def _on_task_failed(self, message: str):
        self.window.set_busy(False)
        self.window.show_error(f"翻译异常: {message}")
        self.toast.show_message(f"翻译异常：{message}", "error")

    # ================= 设置 =================
    def _save_settings(self, cfg: dict):
        """保存完整配置：服务、Key、URL、模型、语言、快捷键。"""
        self.config.set("api.provider", cfg["provider"])
        self.config.set("api.base_url", cfg["base_url"])
        self.config.set("api.model", cfg["model"])
        self.config.set("language.source", cfg["source_lang"])
        self.config.set("language.target", cfg["target_lang"])
        ui_lang = cfg.get("ui_lang", "zh")
        self.config.set("language.ui", ui_lang)
        if cfg.get("overlay_position"):
            self.config.set("overlay.position", cfg["overlay_position"])
        # 自动注入（高风险功能，默认关闭）
        self.config.set("paste.auto_paste", bool(cfg.get("auto_paste", False)))
        self.config.set("paste.delay_ms", int(cfg.get("paste_delay_ms", 10)))
        for key, value in cfg.get("hotkeys", {}).items():
            if value:
                self.config.set(f"hotkeys.{key}", value)
        # 清理已废弃的快捷键动作（如 toggle_overlay），避免旧配置残留导致冲突
        hotkeys_data = self.config.data.get("hotkeys")
        if isinstance(hotkeys_data, dict):
            hotkeys_data.pop("toggle_overlay", None)
        if cfg.get("api_key"):
            self.secret_store.set_key(cfg["api_key"])
        self.config.save()

        # 应用界面语言 + 重新注册快捷键 + 刷新状态胶囊
        self.window.apply_language(ui_lang)
        self._register_hotkeys()
        self._refresh_ui_state()
        self.window.set_status("设置已保存" if ui_lang == "zh" else "Settings saved")

    def _clear_key(self):
        self.secret_store.clear_key()
        self.window.set_status("已清除 API Key")

    def test_connection(self, cfg: dict = None):
        """测试连接：优先用传入的临时配置，否则用已保存配置。"""
        self.window.set_status("测试连接中…")
        if cfg:
            tmp_cfg = {
                "base_url": cfg["base_url"],
                "model": cfg["model"],
                "provider": cfg["provider"],
                "timeout_connect": 8,
                "timeout_read": 15,
            }
            from ..providers import get_provider
            from ..providers.base import ProviderError

            key = cfg.get("api_key") or self.secret_store.get_key()
            try:
                provider_cls = get_provider(cfg["provider"])
                provider = provider_cls(tmp_cfg, key)
                r = provider.test_connection()
            except ProviderError as e:
                self.window.settings_page.set_status(f"[{e.category}] {e.message}", is_error=True)
                self.window.set_status("连接测试失败")
                return
            except Exception as e:
                self.window.settings_page.set_status(f"测试出错: {e}", is_error=True)
                self.window.set_status("连接测试失败")
                return
            self.window.settings_page.set_status(f"连接成功，模型：{r.get('model', '')}")
            self.window.set_status("连接测试完成")
            return

        result = self.translation_service.test_connection()
        if result.get("ok"):
            self.window.settings_page.set_status(f"连接成功，模型：{result.get('model', '')}")
        else:
            self.window.settings_page.set_status(
                f"连接失败: {result.get('error', '')}", is_error=True
            )
        self.window.set_status("连接测试完成")

    def open_log_dir(self):
        """打开日志目录。"""
        import os

        from ..infrastructure.logging_config import get_log_dir

        d = get_log_dir()
        try:
            os.startfile(str(d))
        except Exception as e:
            self.window.set_status(f"无法打开日志目录: {e}")

    # ================= 窗口 / 复制 =================
    def toggle_window(self):
        if self.window.isVisible():
            self.window.hide()
        else:
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()

    def cancel_current(self):
        self.window.hide()

    def copy_last(self):
        text = self.window.translation_page.get_result()
        if not text:
            self.window.set_status("暂无译文可复制")
            return
        if self._copy_to_clipboard(text):
            self.window.set_status("已复制译文")
            self.toast.show_message("已复制译文", "info")
        else:
            self.window.set_status("复制失败")

    def _on_naturalness_change(self, value: int):
        """人性化滑块（0~100）映射为 temperature（0~1.0）。"""
        self._naturalness = value / 100.0

    # ================= 区域选择 =================
    def select_region(self):
        if self._selecting:
            return
        self._selecting = True
        self._selector = RegionSelector()
        self._selector.regionSelected.connect(self._on_region_selected)
        self._selector.cancelled.connect(self._on_region_cancelled)
        self._selector.showFullScreen()

    def _on_region_selected(self, region: dict):
        self._selecting = False
        self.config.set("capture.region", region)
        self.config.save()
        self.window.set_region_state(True)
        self.window.set_status("已保存截图区域")
        self.toast.show_message("截图区域已保存", "ok")

    def _on_region_cancelled(self):
        self._selecting = False
        self.window.set_status("已取消区域选择")

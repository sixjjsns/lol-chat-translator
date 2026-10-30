"""设置页面：翻译服务 / 语言 / 快捷键，用 QTabWidget 分页。

对齐第一版完整功能：
- 翻译服务：服务选择、API Key、Base URL、模型、测试连接
- 语言：源语言（自动识别）、截图翻译目标语言
- 快捷键：6 个动作可自定义 + 恢复默认
"""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ...services.hotkey_service import DEFAULT_HOTKEYS
from ..i18n import tr


class SettingsPage(QWidget):
    """服务配置界面。"""

    saveRequested = Signal(dict)       # 完整配置 dict
    testRequested = Signal(dict)       # 测试连接用的临时配置 dict
    keyCleared = Signal()

    # 快捷键动作 key（文案通过 tr() 取）
    HOTKEY_ACTIONS = [
        "capture_translate",
        "retranslate",
        "copy_last",
        "toggle_window",
        "select_region",
        "reply_translate",
        "cancel",
    ]

    def __init__(self, providers: dict, settings, parent=None):
        super().__init__(parent)
        self._providers = providers  # name -> {name, base_url, model, needs_key}
        self._settings = settings
        self._hotkey_edits = {}
        self._hotkey_labels = {}
        self._build_ui()
        self._load_current()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 16)
        layout.setSpacing(12)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tabs.addTab(self._build_provider_tab(), tr("settings.tab.provider"))
        self.tabs.addTab(self._build_language_tab(), tr("settings.tab.language"))
        self.tabs.addTab(self._build_paste_tab(), tr("settings.tab.paste"))
        self.tabs.addTab(self._build_hotkey_tab(), tr("settings.tab.hotkey"))

        # 底部按钮
        btn_row = QHBoxLayout()
        self.clear_btn = QPushButton(tr("settings.clear_key"))
        self.clear_btn.setObjectName("dangerBtn")
        self.clear_btn.clicked.connect(self._on_clear)
        self.save_btn = QPushButton(tr("settings.save"))
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

        self.status_label = QLabel("")
        self.status_label.setObjectName("muted")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

    # --- 翻译服务页 ---
    def _build_provider_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)

        self.provider_combo = QComboBox()
        for key, meta in self._providers.items():
            self.provider_combo.addItem(meta.get("name", key), key)
        self.provider_combo.currentIndexChanged.connect(self._on_provider_change)
        form.addRow("翻译服务：", self.provider_combo)

        self.provider_hint = QLabel("")
        self.provider_hint.setObjectName("muted")
        self.provider_hint.setWordWrap(True)
        form.addRow("", self.provider_hint)

        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText("输入 API Key（本地 Ollama 无需填写）")
        form.addRow("API Key：", self.key_edit)

        self.base_edit = QLineEdit()
        self.base_edit.setPlaceholderText("https://api.deepseek.com")
        form.addRow("Base URL：", self.base_edit)

        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("deepseek-flash")
        form.addRow("模型：", self.model_edit)

        self.model_hint = QLabel("模型须支持识图/图像输入")
        self.model_hint.setObjectName("muted")
        form.addRow("", self.model_hint)

        layout.addLayout(form)

        self.test_btn = QPushButton(tr("settings.test"))
        self.test_btn.setMinimumWidth(150)
        self.test_btn.clicked.connect(self._on_test)
        test_row = QHBoxLayout()
        test_row.addWidget(self.test_btn)
        test_row.addStretch(1)
        layout.addLayout(test_row)

        layout.addStretch(1)
        return page

    # --- 语言页 ---
    def _build_language_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)

        self.source_combo = QComboBox()
        self.source_label = QLabel(tr("settings.source_lang"))
        form.addRow(self.source_label, self.source_combo)

        self.target_combo = QComboBox()
        self.target_label = QLabel(tr("settings.target_lang"))
        form.addRow(self.target_label, self.target_combo)
        # 两个下拉框都创建后统一填充
        self._fill_lang_combos()

        self.lang_hint = QLabel(tr("settings.lang_hint"))
        self.lang_hint.setObjectName("muted")
        form.addRow("", self.lang_hint)

        # 界面语言
        self.ui_lang_combo = QComboBox()
        self.ui_lang_combo.addItem(tr("ui_lang.zh"), "zh")
        self.ui_lang_combo.addItem(tr("ui_lang.en"), "en")
        self.ui_lang_label = QLabel(tr("settings.ui_lang"))
        form.addRow(self.ui_lang_label, self.ui_lang_combo)

        # 悬浮窗位置
        self.overlay_position_combo = QComboBox()
        for code in ["top-left", "top-right", "bottom-left", "bottom-right"]:
            self.overlay_position_combo.addItem(tr(f"pos.{code.replace('-', '_')}"), code)
        self.overlay_position_label = QLabel(tr("settings.overlay_position"))
        form.addRow(self.overlay_position_label, self.overlay_position_combo)

        layout.addLayout(form)
        layout.addStretch(1)
        return page

    # --- 自动粘贴页（高风险功能） ---
    def _build_paste_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(12)

        self.auto_paste_check = QCheckBox(tr("settings.auto_paste"))
        self.auto_paste_check.setToolTip(tr("settings.auto_paste_warn"))
        form.addRow("", self.auto_paste_check)

        self.paste_delay_spin = QSpinBox()
        self.paste_delay_spin.setRange(1, 500)
        self.paste_delay_spin.setSuffix(" ms")
        self.paste_delay_spin.setValue(10)
        self.paste_delay_label = QLabel(tr("settings.paste_delay"))
        form.addRow(self.paste_delay_label, self.paste_delay_spin)

        layout.addLayout(form)

        self.paste_warn_label = QLabel(tr("settings.auto_paste_warn"))
        self.paste_warn_label.setObjectName("muted")
        self.paste_warn_label.setWordWrap(True)
        self.paste_warn_label.setStyleSheet("color: #e5534b;")
        layout.addWidget(self.paste_warn_label)

        layout.addStretch(1)
        return page

    def _fill_lang_combos(self):
        """填充源语言/目标语言下拉框（语言切换后刷新）。"""
        self.source_combo.clear()
        for code in ["auto", "zh", "en", "ja", "ko"]:
            self.source_combo.addItem(tr(f"lang.{code}"), code)
        self.target_combo.clear()
        for code in ["zh", "en", "ja", "ko"]:
            self.target_combo.addItem(tr(f"lang.{code}"), code)

    # --- 快捷键页 ---
    def _build_hotkey_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(10)

        for key in self.HOTKEY_ACTIONS:
            label = QLabel(tr(f"hotkey.{key}"))
            edit = QLineEdit()
            edit.setPlaceholderText("如 f6 / ctrl+alt+t")
            self._hotkey_edits[key] = edit
            self._hotkey_labels[key] = label
            form.addRow(label, edit)

        layout.addLayout(form)

        self.reset_btn = QPushButton(tr("settings.reset_hotkey"))
        self.reset_btn.clicked.connect(self._reset_hotkeys)
        layout.addWidget(self.reset_btn)

        self.hotkey_hint = QLabel(tr("settings.hotkey_hint"))
        self.hotkey_hint.setObjectName("muted")
        self.hotkey_hint.setWordWrap(True)
        layout.addWidget(self.hotkey_hint)

        layout.addStretch(1)
        return page

    # --- 数据加载 / 交互 ---
    def _load_current(self):
        s = self._settings
        self.provider_combo.setCurrentIndex(
            max(0, self.provider_combo.findData(s.get("api.provider", "deepseek")))
        )
        self.key_edit.setText(s.get("api.base_url", "") and self._get_key() or "")
        self.base_edit.setText(s.get("api.base_url", "https://api.deepseek.com"))
        self.model_edit.setText(s.get("api.model", "deepseek-flash"))
        # 语言
        self.source_combo.setCurrentIndex(
            max(0, self.source_combo.findData(s.get("language.source", "auto")))
        )
        self.target_combo.setCurrentIndex(
            max(0, self.target_combo.findData(s.get("language.target", "zh")))
        )
        self.ui_lang_combo.setCurrentIndex(
            max(0, self.ui_lang_combo.findData(s.get("language.ui", "zh")))
        )
        self.overlay_position_combo.setCurrentIndex(
            max(0, self.overlay_position_combo.findData(s.get("overlay.position", "bottom-right")))
        )
        # 自动粘贴（默认关闭，高风险）
        self.auto_paste_check.setChecked(bool(s.get("paste.auto_paste", False)))
        self.paste_delay_spin.setValue(int(s.get("paste.delay_ms", 10)))
        # 快捷键
        for key, edit in self._hotkey_edits.items():
            edit.setText(s.get(f"hotkeys.{key}", DEFAULT_HOTKEYS.get(key, "")))
        self._on_provider_change()

    def _get_key(self) -> str:
        # 由外部注入 secret_store，这里用占位，实际由 Application 填充
        return self._secret_key if hasattr(self, "_secret_key") else ""

    def set_api_key(self, key: str):
        self._secret_key = key
        self.key_edit.setText(key)

    def _on_provider_change(self):
        key = self.provider_combo.currentData()
        meta = self._providers.get(key, {})
        if meta.get("base_url"):
            self.base_edit.setText(meta["base_url"])
        if meta.get("model"):
            self.model_edit.setText(meta["model"])
        needs_key = meta.get("needs_key", True)
        self.key_edit.setEnabled(needs_key)
        if key == "ollama":
            self.provider_hint.setText(
                "本地模型：需先安装 Ollama 并运行（ollama pull qwen2.5vl:7b），无需 API Key，完全离线免费。"
            )
        elif not needs_key:
            self.provider_hint.setText("该服务无需 API Key。")
        else:
            self.provider_hint.setText("该服务需要 API Key，请在对应平台获取后填入上方。")

    def _on_test(self):
        cfg = self._collect_config()
        self.testRequested.emit(cfg)

    def _on_save(self):
        cfg = self._collect_config()
        # 非 ollama 且无 key 时提示
        if cfg["provider"] != "ollama" and not cfg["api_key"]:
            QMessageBox.warning(self, "提示", "API Key 不能为空（本地 Ollama 无需 Key）")
            return
        self.saveRequested.emit(cfg)

    def _on_clear(self):
        self.key_edit.clear()
        self.keyCleared.emit()

    def _reset_hotkeys(self):
        for key, edit in self._hotkey_edits.items():
            edit.setText(DEFAULT_HOTKEYS.get(key, ""))

    def _collect_config(self) -> dict:
        hotkeys = {k: e.text().strip() for k, e in self._hotkey_edits.items()}
        return {
            "provider": self.provider_combo.currentData(),
            "api_key": self.key_edit.text().strip(),
            "base_url": self.base_edit.text().strip(),
            "model": self.model_edit.text().strip(),
            "source_lang": self.source_combo.currentData(),
            "target_lang": self.target_combo.currentData(),
            "ui_lang": self.ui_lang_combo.currentData(),
            "overlay_position": self.overlay_position_combo.currentData(),
            "auto_paste": self.auto_paste_check.isChecked(),
            "paste_delay_ms": self.paste_delay_spin.value(),
            "hotkeys": hotkeys,
        }

    # --- 供外部调用 ---
    def apply_language(self):
        """刷新文案（语言切换后调用）。"""
        self.tabs.setTabText(0, tr("settings.tab.provider"))
        self.tabs.setTabText(1, tr("settings.tab.language"))
        self.tabs.setTabText(2, tr("settings.tab.paste"))
        self.tabs.setTabText(3, tr("settings.tab.hotkey"))
        self.test_btn.setText(tr("settings.test"))
        self.source_label.setText(tr("settings.source_lang"))
        self.target_label.setText(tr("settings.target_lang"))
        self.lang_hint.setText(tr("settings.lang_hint"))
        self.ui_lang_label.setText(tr("settings.ui_lang"))
        self.overlay_position_label.setText(tr("settings.overlay_position"))
        # 刷新位置下拉框文案（保留当前选中值）
        cur_pos = self.overlay_position_combo.currentData()
        self.overlay_position_combo.clear()
        for code in ["top-left", "top-right", "bottom-left", "bottom-right"]:
            self.overlay_position_combo.addItem(tr(f"pos.{code.replace('-', '_')}"), code)
        self.overlay_position_combo.setCurrentIndex(
            max(0, self.overlay_position_combo.findData(cur_pos))
        )
        self.auto_paste_check.setText(tr("settings.auto_paste"))
        self.auto_paste_check.setToolTip(tr("settings.auto_paste_warn"))
        self.paste_delay_label.setText(tr("settings.paste_delay"))
        self.paste_warn_label.setText(tr("settings.auto_paste_warn"))
        self.reset_btn.setText(tr("settings.reset_hotkey"))
        self.hotkey_hint.setText(tr("settings.hotkey_hint"))
        self.clear_btn.setText(tr("settings.clear_key"))
        self.save_btn.setText(tr("settings.save"))
        for key, label in self._hotkey_labels.items():
            label.setText(tr(f"hotkey.{key}"))

    def set_status(self, text: str, is_error: bool = False):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"color: {'#e5534b' if is_error else '#8b98a8'};"
        )

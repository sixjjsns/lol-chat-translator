"""翻译页面：译文展示 + 反向翻译输入 + 人性化滑块。

布局：
- 顶部操作栏：截取翻译（主按钮）、选择区域、输出语言
- 人性化滑块：带档位标签（直译/偏直译/自然/口语化）
- 译文展示区（只读，可选中复制）
- 反向翻译输入区 + 翻译并复制按钮
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..i18n import get_language, tr


class TranslationPage(QWidget):
    """主翻译界面。"""

    replyRequested = Signal(str, str)     # (text, target_lang)
    naturalnessChanged = Signal(int)      # 0~100
    selectRegionRequested = Signal()
    captureRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ===== 顶部操作栏 =====
        top = QHBoxLayout()
        top.setSpacing(10)

        self.capture_btn = QPushButton(tr("btn.capture"))
        self.capture_btn.setObjectName("primary")
        self.capture_btn.setMinimumHeight(38)
        self.capture_btn.clicked.connect(self.captureRequested.emit)

        self.region_btn = QPushButton(tr("btn.select_region"))
        self.region_btn.setMinimumHeight(38)
        self.region_btn.clicked.connect(self.selectRegionRequested.emit)

        self.lang_label = QLabel(tr("label.output_lang"))
        self.lang_label.setObjectName("muted")
        self.lang_combo = QComboBox()
        self.lang_combo.setMinimumWidth(110)
        self._fill_lang_combo()

        top.addWidget(self.capture_btn)
        top.addWidget(self.region_btn)
        top.addStretch(1)
        top.addWidget(self.lang_label)
        top.addWidget(self.lang_combo)
        layout.addLayout(top)

        # ===== 人性化滑块 =====
        nat_card = QWidget()
        nat_layout = QVBoxLayout(nat_card)
        nat_layout.setContentsMargins(0, 0, 0, 0)
        nat_layout.setSpacing(4)

        nat_row = QHBoxLayout()
        nat_row.setSpacing(10)
        self.nat_title = QLabel(tr("label.naturalness"))
        self.nat_title.setObjectName("muted")
        self.nat_label = QLabel(self._nat_label(70))
        self.nat_label.setObjectName("natValue")

        nat_row.addWidget(self.nat_title)
        nat_row.addStretch(1)
        nat_row.addWidget(self.nat_label)
        nat_layout.addLayout(nat_row)

        slider_row = QHBoxLayout()
        slider_row.setSpacing(10)
        self.left_hint = QLabel(tr("label.literal"))
        self.left_hint.setObjectName("muted")
        self.left_hint.setStyleSheet("font-size: 11px;")
        self.nat_slider = QSlider()
        self.nat_slider.setOrientation(Qt.Orientation.Horizontal)
        self.nat_slider.setRange(0, 100)
        self.nat_slider.setValue(70)
        self.nat_slider.valueChanged.connect(self._on_nat_change)
        self.right_hint = QLabel(tr("label.colloquial"))
        self.right_hint.setObjectName("muted")
        self.right_hint.setStyleSheet("font-size: 11px;")

        slider_row.addWidget(self.left_hint)
        slider_row.addWidget(self.nat_slider, 1)
        slider_row.addWidget(self.right_hint)
        nat_layout.addLayout(slider_row)

        layout.addWidget(nat_card)

        # ===== 译文展示区（可拖动调整大小）=====
        self.result_title = QLabel(tr("label.result"))
        self.result_title.setObjectName("sectionTitle")
        layout.addWidget(self.result_title)

        # 用 QSplitter 让译文区和回复区可拖动调整大小
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        result_container = QWidget()
        result_layout = QVBoxLayout(result_container)
        result_layout.setContentsMargins(0, 0, 0, 0)
        self.result_edit = QTextEdit()
        self.result_edit.setReadOnly(True)
        self.result_edit.setPlaceholderText(tr("placeholder.result"))
        result_layout.addWidget(self.result_edit)

        reply_container = QWidget()
        reply_layout = QVBoxLayout(reply_container)
        reply_layout.setContentsMargins(0, 0, 0, 0)
        reply_layout.setSpacing(8)

        self.reply_title = QLabel(tr("label.reply"))
        self.reply_title.setObjectName("sectionTitle")
        reply_layout.addWidget(self.reply_title)

        self.reply_edit = QTextEdit()
        self.reply_edit.setPlaceholderText(tr("placeholder.reply"))
        self.reply_edit.setMinimumHeight(60)
        reply_layout.addWidget(self.reply_edit)

        reply_btn_row = QHBoxLayout()
        self.reply_hint = QLabel("")
        self.reply_hint.setObjectName("muted")
        self.reply_btn = QPushButton(tr("btn.reply"))
        self.reply_btn.setObjectName("primary")
        self.reply_btn.setMinimumHeight(36)
        self.reply_btn.clicked.connect(self._on_reply)
        reply_btn_row.addWidget(self.reply_hint)
        reply_btn_row.addStretch(1)
        reply_btn_row.addWidget(self.reply_btn)
        reply_layout.addLayout(reply_btn_row)

        splitter.addWidget(result_container)
        splitter.addWidget(reply_container)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        # 初始尺寸比例
        splitter.setSizes([360, 160])
        layout.addWidget(splitter, 1)

    def _fill_lang_combo(self):
        self.lang_combo.clear()
        self.lang_combo.addItem(tr("lang.zh"), "zh")
        self.lang_combo.addItem(tr("lang.en"), "en")
        self.lang_combo.addItem(tr("lang.ja"), "ja")
        self.lang_combo.addItem(tr("lang.ko"), "ko")

    def apply_language(self):
        """刷新文案（语言切换后调用）。"""
        self.capture_btn.setText(tr("btn.capture"))
        self.region_btn.setText(tr("btn.select_region"))
        self.lang_label.setText(tr("label.output_lang"))
        self._fill_lang_combo()
        self.nat_title.setText(tr("label.naturalness"))
        self.left_hint.setText(tr("label.literal"))
        self.right_hint.setText(tr("label.colloquial"))
        self.result_title.setText(tr("label.result"))
        self.result_edit.setPlaceholderText(tr("placeholder.result"))
        self.reply_title.setText(tr("label.reply"))
        self.reply_edit.setPlaceholderText(tr("placeholder.reply"))
        self.reply_btn.setText(tr("btn.reply"))
        self.nat_label.setText(self._nat_label(self.nat_slider.value()))

    def _on_nat_change(self, value: int):
        self.nat_label.setText(self._nat_label(value))
        self.naturalnessChanged.emit(value)

    @staticmethod
    def _nat_label(value: int) -> str:
        if get_language() == "en":
            if value < 25:
                return "Literal"
            if value < 50:
                return "Semi-literal"
            if value < 75:
                return "Natural"
            return "Colloquial"
        if value < 25:
            return "直译"
        if value < 50:
            return "偏直译"
        if value < 75:
            return "自然"
        return "口语化"

    def _on_reply(self):
        text = self.reply_edit.toPlainText().strip()
        if not text:
            self.reply_hint.setText(tr("hint.reply_empty"))
            return
        target = self.lang_combo.currentData()
        self.reply_hint.setText(tr("hint.reply_ing"))
        self.replyRequested.emit(text, target)

    # --- 供外部调用 ---
    def set_result(self, text: str):
        self.result_edit.setPlainText(text)

    def get_result(self) -> str:
        return self.result_edit.toPlainText().strip()

    def get_target_lang(self) -> str:
        return self.lang_combo.currentData()

    def get_naturalness(self) -> int:
        return self.nat_slider.value()

    def clear_result(self):
        self.result_edit.clear()

    def set_reply_result(self, text: str):
        """反向翻译结果写入输入框（便于复制），并更新提示。"""
        self.reply_edit.setPlainText(text)
        self.reply_hint.setText(tr("hint.reply_done"))

    def clear_reply_hint(self):
        self.reply_hint.setText("")

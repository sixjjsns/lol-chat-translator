"""翻译页（v1.2.0 重制）：卡片式双区布局 + 快捷短语。

布局
----
::

    [ 截取聊天 ] [ 选区域 ] [区域状态]          语气 ——●—— 自然   中文 ▾
    ┌──────────────────────────────────────────────────────────┐
    │ ● 队友在说什么            F6        [耗时] [重译] [复制]  │
    │   译文（最近 5 条，带时间戳）                              │
    └──────────────────────────────────────────────────────────┘
    ┌──────────────────────────────────────────────────────────┐
    │ ● 我要回什么                           [自动注入 · 开]     │
    │   输入框（中文）                                          │
    │   快捷短语  [来中路抓] [打野在下方] [我去做视野] ...       │
    │   将发送：…                              [翻译并注入]     │
    └──────────────────────────────────────────────────────────┘

设计取舍
--------
- 译文区用 HTML 渲染，带时间戳和分隔线，连续 F6 时上下文更好读。
- 回复区保留输入框（在**主窗口**里，不在游戏里），这是 v1.2.0 删掉
  “游戏内 F10 输入悬浮窗”后唯一的中文输入位置。
- “将发送”预览独立一行：翻译结果不再覆盖输入框，方便改完再发。
"""

from __future__ import annotations

import html
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..i18n import get_language, tr

# 一键短语：LoL 里最高频的几句，点一下直接翻译并注入
QUICK_PHRASES = [
    "来中路抓一下",
    "打野在下路",
    "我去做视野",
    "别送，稳住",
    "抱团推塔",
    "打得不错",
]


def _chip(text: str, style: str = "chip") -> QLabel:
    label = QLabel(text)
    label.setObjectName(style)
    return label


class TranslationPage(QWidget):
    """主翻译界面。"""

    replyRequested = Signal(str, str)     # (text, target_lang)
    naturalnessChanged = Signal(int)      # 0~100
    selectRegionRequested = Signal()
    captureRequested = Signal()
    retranslateRequested = Signal()
    copyRequested = Signal()

    MAX_HISTORY = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history: list[tuple[str, str]] = []
        self._last_reply_out = ""
        self._auto_paste = False
        self._build_ui()

    # ================= 构建 =================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 18, 22, 16)
        root.setSpacing(14)

        root.addLayout(self._build_action_row())
        root.addWidget(self._build_result_card(), 3)
        root.addWidget(self._build_reply_card(), 2)

    def _build_action_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)

        self.capture_btn = QPushButton("📷  " + tr("btn.capture"))
        self.capture_btn.setObjectName("primaryBtn")
        self.capture_btn.setMinimumHeight(42)
        self.capture_btn.setMinimumWidth(158)
        self.capture_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.capture_btn.setToolTip(tr("tip.capture"))
        self.capture_btn.clicked.connect(self.captureRequested.emit)

        self.region_btn = QPushButton(tr("btn.select_region"))
        self.region_btn.setObjectName("ghostBtn")
        self.region_btn.setMinimumHeight(42)
        self.region_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.region_btn.clicked.connect(self.selectRegionRequested.emit)

        self.region_chip = _chip(tr("chip.region_unset"), "chipWarn")

        # 语气滑杆（temperature），越靠右越口语化
        self.nat_label = QLabel(tr("label.naturalness_short"))
        self.nat_label.setObjectName("cardHint")
        self.nat_slider = QSlider(Qt.Orientation.Horizontal)
        self.nat_slider.setRange(0, 100)
        self.nat_slider.setValue(70)
        self.nat_slider.setFixedWidth(104)
        self.nat_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.nat_slider.valueChanged.connect(self._on_nat_change)
        self.nat_value = QLabel(self._nat_label(70))
        self.nat_value.setObjectName("cardHint")
        self.nat_value.setMinimumWidth(44)

        self.lang_label = QLabel(tr("label.output_lang"))
        self.lang_label.setObjectName("cardHint")
        self.lang_combo = QComboBox()
        self.lang_combo.setMinimumWidth(104)
        self._fill_lang_combo()

        row.addWidget(self.capture_btn)
        row.addWidget(self.region_btn)
        row.addWidget(self.region_chip)
        row.addStretch(1)
        row.addWidget(self.nat_label)
        row.addWidget(self.nat_slider)
        row.addWidget(self.nat_value)
        row.addSpacing(6)
        row.addWidget(self.lang_label)
        row.addWidget(self.lang_combo)
        return row

    def _build_result_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(8)

        dot = QLabel("●")
        dot.setObjectName("dotGold")
        self.result_title = QLabel(tr("card.result_title"))
        self.result_title.setObjectName("cardTitle")
        self.result_hint = QLabel(tr("card.result_hint"))
        self.result_hint.setObjectName("cardHint")

        self.duration_chip = _chip("", "chip")
        self.duration_chip.hide()

        self.retranslate_btn = QPushButton(tr("btn.retranslate"))
        self.retranslate_btn.setObjectName("ghostBtn")
        self.retranslate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retranslate_btn.setToolTip("F7")
        self.retranslate_btn.clicked.connect(self.retranslateRequested.emit)

        self.copy_btn = QPushButton(tr("btn.copy"))
        self.copy_btn.setObjectName("ghostBtn")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setToolTip("F8")
        self.copy_btn.clicked.connect(self.copyRequested.emit)

        head.addWidget(dot)
        head.addWidget(self.result_title)
        head.addWidget(self.result_hint)
        head.addStretch(1)
        head.addWidget(self.duration_chip)
        head.addWidget(self.retranslate_btn)
        head.addWidget(self.copy_btn)
        layout.addLayout(head)

        self.result_edit = QTextEdit()
        self.result_edit.setReadOnly(True)
        self.result_edit.setPlaceholderText(tr("placeholder.result"))
        self.result_edit.setMinimumHeight(140)
        layout.addWidget(self.result_edit, 1)

        return card

    def _build_reply_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        head = QHBoxLayout()
        head.setSpacing(8)
        dot = QLabel("●")
        dot.setObjectName("dotGreen")
        self.reply_title = QLabel(tr("card.reply_title"))
        self.reply_title.setObjectName("cardTitle")
        self.reply_hint = QLabel(tr("card.reply_hint"))
        self.reply_hint.setObjectName("cardHint")

        self.inject_chip = _chip(tr("chip.inject_off"), "chip")

        head.addWidget(dot)
        head.addWidget(self.reply_title)
        head.addWidget(self.reply_hint)
        head.addStretch(1)
        head.addWidget(self.inject_chip)
        layout.addLayout(head)

        self.reply_edit = QTextEdit()
        self.reply_edit.setPlaceholderText(tr("placeholder.reply"))
        self.reply_edit.setMinimumHeight(56)
        self.reply_edit.setMaximumHeight(92)
        layout.addWidget(self.reply_edit)

        # 快捷短语网格（3 列 × 2 行，宽度不够也不会挤爆）
        phrase_label = QLabel(tr("label.quick_phrases"))
        phrase_label.setObjectName("cardHint")
        phrase_wrap = QVBoxLayout()
        phrase_wrap.setSpacing(6)
        phrase_wrap.addWidget(phrase_label)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        self._phrase_buttons: list[QPushButton] = []
        for index, phrase in enumerate(QUICK_PHRASES):
            btn = QPushButton(phrase)
            btn.setObjectName("chipBtn")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, p=phrase: self._on_phrase(p))
            grid.addWidget(btn, index // 3, index % 3)
            self._phrase_buttons.append(btn)
        for col in range(3):
            grid.setColumnStretch(col, 1)
        phrase_wrap.addLayout(grid)
        layout.addLayout(phrase_wrap)

        bottom = QHBoxLayout()
        bottom.setSpacing(10)

        self.preview_label = QLabel(tr("label.preview_empty"))
        self.preview_label.setObjectName("cardHint")
        self.preview_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.reply_btn = QPushButton(tr("btn.reply_copy"))
        self.reply_btn.setObjectName("primaryBtn")
        self.reply_btn.setMinimumHeight(38)
        self.reply_btn.setMinimumWidth(148)
        self.reply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reply_btn.clicked.connect(self._on_reply)

        bottom.addWidget(self.preview_label, 1)
        bottom.addWidget(self.reply_btn)
        layout.addLayout(bottom)

        return card

    # ================= 语言 / 交互 =================
    def _fill_lang_combo(self):
        current = self.lang_combo.currentData() if self.lang_combo.count() else "zh"
        self.lang_combo.clear()
        self.lang_combo.addItem(tr("lang.zh"), "zh")
        self.lang_combo.addItem(tr("lang.en"), "en")
        self.lang_combo.addItem(tr("lang.ja"), "ja")
        self.lang_combo.addItem(tr("lang.ko"), "ko")
        self.lang_combo.setCurrentIndex(max(0, self.lang_combo.findData(current)))

    def _on_phrase(self, phrase: str):
        self.reply_edit.setPlainText(phrase)
        self._on_reply()

    def _on_reply(self):
        text = self.reply_edit.toPlainText().strip()
        if not text:
            self.set_preview(tr("hint.reply_empty"), error=True)
            return
        target = self.lang_combo.currentData()
        self.reply_btn.setEnabled(False)
        self.reply_btn.setText(tr("hint.reply_ing"))
        self.replyRequested.emit(text, target)

    def _on_nat_change(self, value: int):
        self.nat_value.setText(self._nat_label(value))
        self.naturalnessChanged.emit(value)

    @staticmethod
    def _nat_label(value: int) -> str:
        if get_language() == "en":
            if value < 25:
                return "Literal"
            if value < 50:
                return "Semi"
            if value < 75:
                return "Natural"
            return "Casual"
        if value < 25:
            return "直译"
        if value < 50:
            return "偏直译"
        if value < 75:
            return "自然"
        return "口语化"

    # ================= 状态 =================
    def set_auto_paste(self, enabled: bool):
        self._auto_paste = bool(enabled)
        self.inject_chip.setText(
            tr("chip.inject_on") if enabled else tr("chip.inject_off")
        )
        self.inject_chip.setObjectName("chipOk" if enabled else "chip")
        self.inject_chip.style().unpolish(self.inject_chip)
        self.inject_chip.style().polish(self.inject_chip)
        self.reply_btn.setText(tr("btn.reply_inject") if enabled else tr("btn.reply_copy"))

    def set_region_state(self, has_region: bool):
        self.region_chip.setText(tr("chip.region_set") if has_region else tr("chip.region_unset"))
        self.region_chip.setObjectName("chipGold" if has_region else "chipWarn")
        self.region_chip.style().unpolish(self.region_chip)
        self.region_chip.style().polish(self.region_chip)

    def set_busy(self, busy: bool):
        self.capture_btn.setEnabled(not busy)
        self.retranslate_btn.setEnabled(not busy)
        if not busy:
            self.reply_btn.setEnabled(True)
            self.reply_btn.setText(
                tr("btn.reply_inject") if self._auto_paste else tr("btn.reply_copy")
            )

    def set_duration(self, detail: str):
        if detail:
            self.duration_chip.setText(detail)
            self.duration_chip.show()
        else:
            self.duration_chip.hide()

    # ================= 译文历史 =================
    def set_result(self, text: str):
        """追加一条译文，最多保留 MAX_HISTORY 条，新的一条在底部。"""
        text = (text or "").strip()
        if not text:
            return
        stamp = datetime.now().strftime("%H:%M:%S")
        self._history.append((stamp, text))
        if len(self._history) > self.MAX_HISTORY:
            self._history = self._history[-self.MAX_HISTORY:]
        self._render_history()

    def _render_history(self):
        if not self._history:
            self.result_edit.clear()
            return

        blocks = []
        for index, (stamp, text) in enumerate(self._history):
            body = html.escape(text).replace("\n", "<br/>")
            if index:
                blocks.append(
                    '<div style="color:#233047; font-size:10px; margin:8px 0;">────────────'
                    + '────────────────────────</div>'
                )
            blocks.append(
                f'<div style="color:#64748B; font-size:11px; margin-bottom:3px;">{stamp}</div>'
                f'<div style="color:#E9EFF7; font-size:13px; line-height:150%;">{body}</div>'
            )

        self.result_edit.setHtml("".join(blocks))
        cursor = self.result_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.result_edit.setTextCursor(cursor)

    def get_result(self) -> str:
        """最新一条译文（复制快捷键用）。"""
        if self._history:
            return self._history[-1][1]
        return ""

    def clear_result(self):
        self._history.clear()
        self.result_edit.clear()
        self.duration_chip.hide()

    # ================= 回复 =================
    def set_reply_result(self, text: str):
        """翻译完成：更新“将发送”预览，并把按钮恢复可用。"""
        self._last_reply_out = (text or "").strip()
        self.reply_btn.setEnabled(True)
        self.reply_btn.setText(
            tr("btn.reply_inject") if self._auto_paste else tr("btn.reply_copy")
        )
        if self._last_reply_out:
            preview = self._last_reply_out.replace("\n", " / ")
            if len(preview) > 44:
                preview = preview[:44] + "…"
            self.set_preview(tr("label.preview_done").format(text=preview))
        else:
            self.set_preview(tr("hint.reply_empty_out"), error=True)

    def set_preview(self, text: str, error: bool = False):
        self.preview_label.setText(text)
        color = "#F87171" if error else "#93A3B8"
        self.preview_label.setStyleSheet(f"color: {color}; font-size: 11px;")

    def get_reply_out(self) -> str:
        return self._last_reply_out

    def get_reply_text(self) -> str:
        return self.reply_edit.toPlainText().strip()

    def clear_reply_hint(self):
        self.set_preview(tr("label.preview_empty"))

    # ================= 取值 =================
    def get_target_lang(self) -> str:
        return self.lang_combo.currentData()

    def get_naturalness(self) -> int:
        return self.nat_slider.value()

    # ================= 语言刷新 =================
    def apply_language(self):
        self.capture_btn.setText("📷  " + tr("btn.capture"))
        self.region_btn.setText(tr("btn.select_region"))
        self.lang_label.setText(tr("label.output_lang"))
        self._fill_lang_combo()
        self.nat_label.setText(tr("label.naturalness_short"))
        self.nat_value.setText(self._nat_label(self.nat_slider.value()))

        self.result_title.setText(tr("card.result_title"))
        self.result_hint.setText(tr("card.result_hint"))
        self.retranslate_btn.setText(tr("btn.retranslate"))
        self.copy_btn.setText(tr("btn.copy"))
        self.result_edit.setPlaceholderText(tr("placeholder.result"))

        self.reply_title.setText(tr("card.reply_title"))
        self.reply_hint.setText(tr("card.reply_hint"))
        self.reply_edit.setPlaceholderText(tr("placeholder.reply"))
        self.set_auto_paste(self._auto_paste)
        self.clear_reply_hint()
        self._render_history()

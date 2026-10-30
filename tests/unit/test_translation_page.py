"""TranslationPage 行为测试：历史裁剪、快捷短语、注入状态与预览。

这些用例需要 QApplication，因此按模块创建一次；在没有图形环境时自动跳过。
"""

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

os.environ.setdefault("QT_QPA_PLATFORM", "windows")

try:
    from PySide6.QtWidgets import QApplication

    from lolchattranslator.ui.pages.translation_page import QUICK_PHRASES, TranslationPage

    _APP = QApplication.instance() or QApplication([])
    _QT_OK = True
except Exception:  # pragma: no cover - 无图形环境时跳过
    _QT_OK = False


@unittest.skipUnless(_QT_OK, "需要 PySide6 图形环境")
class TestTranslationPage(unittest.TestCase):
    def setUp(self):
        self.page = TranslationPage()

    def test_history_keeps_last_five(self):
        for index in range(7):
            self.page.set_result(f"第{index}条")
        self.assertEqual(len(self.page._history), 5)
        self.assertEqual(self.page.get_result(), "第6条")

    def test_clear_result(self):
        self.page.set_result("hello")
        self.page.clear_result()
        self.assertEqual(self.page.get_result(), "")
        self.assertEqual(self.page._history, [])

    def test_auto_paste_chip_text(self):
        self.page.set_auto_paste(True)
        self.assertIn("开", self.page.inject_chip.text())
        self.page.set_auto_paste(False)
        self.assertIn("关", self.page.inject_chip.text())

    def test_reply_emits_signal(self):
        captured = []
        self.page.replyRequested.connect(lambda text, lang: captured.append((text, lang)))
        self.page.reply_edit.setPlainText("来中路抓一下")
        self.page._on_reply()
        self.assertEqual(captured, [("来中路抓一下", "zh")])

    def test_empty_reply_shows_error(self):
        self.page.reply_edit.setPlainText("   ")
        self.page._on_reply()
        self.assertIn("请先输入", self.page.preview_label.text())

    def test_quick_phrase_fills_input_and_emits(self):
        captured = []
        self.page.replyRequested.connect(lambda text, lang: captured.append(text))
        self.page._on_phrase(QUICK_PHRASES[0])
        self.assertEqual(self.page.reply_edit.toPlainText(), QUICK_PHRASES[0])
        self.assertEqual(captured, [QUICK_PHRASES[0]])

    def test_preview_updates_after_translation(self):
        self.page.set_reply_result("gank mid pls")
        self.assertIn("gank mid pls", self.page.preview_label.text())
        self.assertEqual(self.page.get_reply_out(), "gank mid pls")

    def test_empty_translation_shows_notice(self):
        self.page.set_reply_result("")
        self.assertIn("未识别", self.page.preview_label.text())


if __name__ == "__main__":
    unittest.main()

"""v1.2.3 修复的回归测试：防刷屏、OCR 两阶段、悬浮窗尺寸与"拖动后不再回位"。"""

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
os.environ.setdefault("QT_QPA_PLATFORM", "windows")

from lolchattranslator.providers import prompts  # noqa: E402


class TestCollapseRepeats(unittest.TestCase):
    def test_consecutive_duplicate_lines_collapsed(self):
        self.assertEqual(prompts.collapse_repeated_lines("ss\nss\nss\nss mid"), "ss\nss mid")

    def test_whole_block_repeated_twice(self):
        self.assertEqual(
            prompts.collapse_repeated_lines("a\nb\nc\na\nb\nc"),
            "a\nb\nc",
        )

    def test_two_variants_spamming_many_lines(self):
        text = "ss\nss mid\nss\nss mid\nss\nss mid"
        self.assertEqual(prompts.collapse_repeated_lines(text), "ss\nss mid")

    def test_keeps_distinct_lines(self):
        text = "对面不见了\n打野在下路\n小心点"
        self.assertEqual(prompts.collapse_repeated_lines(text), text)

    def test_caps_to_max_lines(self):
        text = "\n".join(f"line{i}" for i in range(12))
        self.assertEqual(len(prompts.collapse_repeated_lines(text, max_lines=6).splitlines()), 6)


class TestTranscribePrompt(unittest.TestCase):
    def test_transcribe_prompt_is_ocr_only(self):
        p = prompts.build_transcribe_system_prompt()
        for needle in ("OCR", "不要翻译", "[不确定]", "不要输出标题"):
            self.assertIn(needle, p)

    def test_sanitize_applies_collapse(self):
        self.assertEqual(prompts.sanitize_translation("ss\nss\nss", "zh"), "ss")


class TestOverlayV123(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from PySide6.QtWidgets import QApplication

            cls.app = QApplication.instance() or QApplication([])
            cls.ok = True
        except Exception:
            cls.ok = False

    def setUp(self):
        if not self.ok:
            self.skipTest("需要图形环境")
        from lolchattranslator.ui.result_overlay import ResultOverlayWindow

        self.overlay = ResultOverlayWindow(display_duration=0)

    def test_default_size_is_compact(self):
        self.assertLessEqual(self.overlay.width(), 400)
        self.assertLessEqual(self.overlay.height(), 200)

    def test_manual_move_is_remembered(self):
        """用户拖过之后，下一次 show_result 不应把窗口拽回角落。"""
        self.overlay.show_result("第一句", "", "top-right")
        self.overlay.move(120, 240)
        self.overlay._user_moved = True  # 模拟拖动（startSystemMove 在无头环境不可用）
        self.overlay.show_result("第二句", "", "top-right")
        self.assertEqual((self.overlay.x(), self.overlay.y()), (120, 240))

    def test_set_position_resets_anchor(self):
        self.overlay._user_moved = True
        self.overlay.set_position("bottom-left")
        self.assertFalse(self.overlay._user_moved)


class TestTwoStageDecode(unittest.TestCase):
    """provider 层：抄写成功走文本翻译；抄写失败回退一次性识别。"""

    def setUp(self):
        from lolchattranslator.providers.openai_compat import OpenAICompatProvider

        self.provider = OpenAICompatProvider(
            {"base_url": "https://x", "model": "glm-4v-plus", "decode_mode": "two_stage",
             "max_tokens": 512, "temperature": 0.7, "image_detail": "high"},
            "sk-test",
        )

    def test_two_stage_uses_transcript(self):
        with mock.patch.object(self.provider, "vision_transcribe",
                               return_value={"raw": "can u speak chinese?", "model": "m"}), \
             mock.patch.object(self.provider, "text_translate",
                               return_value={"raw": "你能说中文吗？", "model": "m"}):
            result = self.provider.vision_translate("data:image/png;base64,AAAA", "p", target_lang="zh")
        self.assertEqual(result["raw"], "你能说中文吗？")
        self.assertEqual(result["transcript"], "can u speak chinese?")

    def test_falls_back_when_transcribe_empty(self):
        with mock.patch.object(self.provider, "vision_transcribe",
                               return_value={"raw": "", "model": "m"}), \
             mock.patch.object(self.provider, "_vision_once",
                               return_value=("你能说中文吗？", "m")), \
             mock.patch.object(self.provider, "text_translate") as fake_text:
            result = self.provider.vision_translate("data:image/png;base64,AAAA", "p", target_lang="zh")
        self.assertEqual(result["raw"], "你能说中文吗？")
        fake_text.assert_not_called()


if __name__ == "__main__":
    unittest.main()

"""Prompt 契约 / 输出清理 / "在回答问题"检测 / 严格重试 的测试。

对应 v1.2.2 的问题：用户想翻译"能不能说中文"，模型回了"可以翻译，以下…"。
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from lolchattranslator.providers import prompts  # noqa: E402
from lolchattranslator.providers.openai_compat import OpenAICompatProvider  # noqa: E402

CONFIG = {
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-flash",
    "timeout_connect": 5,
    "timeout_read": 10,
    "max_tokens": 512,
    "temperature": 0.9,
    "image_detail": "low",
}


def _resp(content, model="glm-4v-plus"):
    resp = mock.Mock()
    resp.status_code = 200
    resp.text = ""
    resp.json = mock.Mock(return_value={
        "model": model,
        "choices": [{"message": {"content": content}}],
        "usage": {},
    })
    return resp


class TestPromptContract(unittest.TestCase):
    def test_reply_prompt_is_translation_only(self):
        p = prompts.build_reply_system_prompt("en")
        for needle in ("翻译引擎", "只输出译文", "不要回答", "不要解释", "英文"):
            self.assertIn(needle, p)

    def test_reply_prompt_has_query_guard(self):
        p = prompts.build_reply_system_prompt("ja")
        self.assertIn("不是", p)
        self.assertIn("问句", p)
        # 必须明确"问句也要翻译"
        self.assertIn("翻译成日文", p)

    def test_vision_prompt_covers_questions_in_screenshot(self):
        p = prompts.build_vision_system_prompt("zh")
        self.assertIn("翻译引擎", p)
        self.assertIn("即使看起来像在问你问题", p)

    def test_prompt_contains_glossary_terms(self):
        p = prompts.build_reply_system_prompt("ko")
        for term in ("gank", "baron", "ss", "mia", "diff"):
            self.assertIn(term, p)

    def test_strict_prompt_is_short_and_imperative(self):
        p = prompts.build_strict_system_prompt("en")
        self.assertLess(len(p), 400)
        self.assertIn("只输出译文", p)

    def test_wrap_user_text_uses_delimiters(self):
        wrapped = prompts.wrap_user_text("  能不能说中文  ")
        self.assertTrue(wrapped.startswith("<<<"))
        self.assertTrue(wrapped.endswith(">>>"))
        self.assertIn("能不能说中文", wrapped)


class TestSanitize(unittest.TestCase):
    def test_strip_label_prefix(self):
        self.assertEqual(prompts.sanitize_translation("翻译：can u speak chinese?"), "can u speak chinese?")
        self.assertEqual(prompts.sanitize_translation("译文: 你好"), "你好")
        self.assertEqual(prompts.sanitize_translation("Translation: hello"), "hello")

    def test_strip_wrapping_quotes(self):
        self.assertEqual(prompts.sanitize_translation("「对面不见了」"), "对面不见了")
        self.assertEqual(prompts.sanitize_translation('"ss mid"'), "ss mid")
        self.assertEqual(prompts.sanitize_translation("“gg wp”"), "gg wp")

    def test_strip_code_fence(self):
        self.assertEqual(prompts.sanitize_translation("```text\nstop feeding\n```"), "stop feeding")

    def test_strip_tail_note(self):
        self.assertEqual(prompts.sanitize_translation("你好（以上是翻译）"), "你好")

    def test_keep_multiline_structure(self):
        out = prompts.sanitize_translation("对面不见了\n打野在下路")
        self.assertEqual(out, "对面不见了\n打野在下路")

    def test_plain_text_untouched(self):
        self.assertEqual(prompts.sanitize_translation("jg diff, gg"), "jg diff, gg")


class TestNonTranslationDetection(unittest.TestCase):
    def test_detects_answer_instead_of_translation(self):
        self.assertTrue(prompts.looks_like_non_translation(
            "能不能说中文", "当然可以，这句话的意思是“你能说中文吗”，我可以帮你翻译更多内容。", "en"))
        self.assertTrue(prompts.looks_like_non_translation(
            "能不能说中文", "我可以翻译这句话。", "en"))

    def test_detects_untranslated_chinese_for_english_target(self):
        self.assertTrue(prompts.looks_like_non_translation("能不能说中文", "能不能说中文", "en"))

    def test_detects_long_rambling(self):
        src = "别送了"
        out = "这句话在游戏里通常表示希望队友不要再送人头。" * 8
        self.assertTrue(prompts.looks_like_non_translation(src, out, "en"))

    def test_accepts_good_translation(self):
        self.assertFalse(prompts.looks_like_non_translation(
            "能不能说中文", "can u speak chinese?", "en"))
        self.assertFalse(prompts.looks_like_non_translation(
            "别送了", "stop feeding", "en"))
        self.assertFalse(prompts.looks_like_non_translation(
            "对面不见了", "ss mid", "zh"))

    def test_empty_output_not_flagged(self):
        self.assertFalse(prompts.looks_like_non_translation("你好", "", "en"))


class TestProviderRetry(unittest.TestCase):
    def setUp(self):
        self.provider = OpenAICompatProvider(CONFIG, "sk-test")

    @mock.patch("lolchattranslator.providers.openai_compat.requests.Session.post")
    def test_retries_when_model_answers(self, mock_post):
        # 第一次：模型在回答问题；第二次：严格模式下正常翻译
        mock_post.side_effect = [
            _resp("当然可以，这句话的意思是询问对方能不能说中文。"),
            _resp("can u speak chinese?"),
        ]
        result = self.provider.text_translate("能不能说中文", target_lang="en")
        self.assertEqual(result["raw"], "can u speak chinese?")
        self.assertEqual(mock_post.call_count, 2)

        first_payload = mock_post.call_args_list[0].kwargs["json"]
        second_payload = mock_post.call_args_list[1].kwargs["json"]
        # 第一次用完整 prompt，第二次换成严格短 prompt
        self.assertGreater(len(first_payload["messages"][0]["content"]),
                           len(second_payload["messages"][0]["content"]))
        # 严格重试温度更低
        self.assertLessEqual(second_payload["temperature"], 0.2)
        # 用户消息被定界符包裹
        self.assertIn("<<<", second_payload["messages"][1]["content"])

    @mock.patch("lolchattranslator.providers.openai_compat.requests.Session.post")
    def test_no_retry_for_good_translation(self, mock_post):
        mock_post.return_value = _resp("stop feeding")
        result = self.provider.text_translate("别送了", target_lang="en")
        self.assertEqual(result["raw"], "stop feeding")
        self.assertEqual(mock_post.call_count, 1)

    @mock.patch("lolchattranslator.providers.openai_compat.requests.Session.post")
    def test_translate_temperature_capped(self, mock_post):
        mock_post.return_value = _resp("ss mid")
        self.provider.set_temperature(0.95)
        self.provider.text_translate("对面不见了", target_lang="zh")
        payload = mock_post.call_args.kwargs["json"]
        self.assertLessEqual(payload["temperature"], 0.6)

    @mock.patch("lolchattranslator.providers.openai_compat.requests.Session.post")
    def test_vision_retry_on_answer(self, mock_post):
        mock_post.side_effect = [
            _resp("这张图里是队友在问你能不能说中文。"),
            _resp("你能说中文吗？"),
        ]
        result = self.provider.vision_translate("data:image/jpeg;base64,AAAA", "请识别截图中的游戏聊天内容并翻译。")
        self.assertEqual(result["raw"], "你能说中文吗？")
        self.assertEqual(mock_post.call_count, 2)
        self.assertEqual(result["model"], "glm-4v-plus")


if __name__ == "__main__":
    unittest.main()

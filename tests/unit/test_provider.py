"""Provider 测试：错误分类与请求格式（mock HTTP）。"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from lolchattranslator.providers import OpenAICompatProvider, ProviderError  # noqa: E402

CONFIG = {
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-flash",
    "timeout_connect": 5,
    "timeout_read": 10,
    "max_tokens": 100,
    "temperature": 0.7,
    "image_detail": "low",
}


def _fake_response(status, body):
    resp = mock.Mock()
    resp.status_code = status
    resp.text = body
    resp.json = mock.Mock(return_value=body if isinstance(body, dict) else {})
    return resp


class TestOpenAICompatProvider(unittest.TestCase):
    def setUp(self):
        self.provider = OpenAICompatProvider(CONFIG, "sk-test")

    def test_classify_auth(self):
        err = self.provider._classify_error(401, "unauthorized")
        self.assertEqual(err.category, "auth")

    def test_classify_quota_429(self):
        err = self.provider._classify_error(429, "rate limit")
        self.assertEqual(err.category, "quota")

    def test_classify_server_5xx(self):
        err = self.provider._classify_error(500, "internal error")
        self.assertEqual(err.category, "server")

    def test_classify_model_unavailable(self):
        err = self.provider._classify_error(400, "this model does not support image")
        self.assertEqual(err.category, "model_unavailable")

    @mock.patch("lolchattranslator.providers.openai_compat.requests.Session.post")
    def test_chat_success(self, mock_post):
        mock_post.return_value = _fake_response(200, {
            "model": "deepseek-flash",
            "choices": [{"message": {"content": "hello"}}],
            "usage": {},
        })
        data = self.provider.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(data["choices"][0]["message"]["content"], "hello")

    @mock.patch("lolchattranslator.providers.openai_compat.requests.Session.post")
    def test_vision_translate_request_shape(self, mock_post):
        mock_post.return_value = _fake_response(200, {
            "model": "deepseek-flash",
            "choices": [{"message": {"content": "翻译结果"}}],
            "usage": {},
        })
        result = self.provider.vision_translate("data:image/jpeg;base64,AAAA", "翻译")
        self.assertEqual(result["status"], "success")
        call_args = mock_post.call_args
        payload = call_args.kwargs.get("json") or call_args[1]["json"]
        user_content = payload["messages"][1]["content"]
        self.assertTrue(any(block.get("type") == "image_url" for block in user_content))
        self.assertTrue(any(block.get("type") == "text" for block in user_content))

    @mock.patch("lolchattranslator.providers.openai_compat.requests.Session.post")
    def test_text_translate(self, mock_post):
        mock_post.return_value = _fake_response(200, {
            "model": "deepseek-flash",
            "choices": [{"message": {"content": "mid, gank top please"}}],
            "usage": {},
        })
        result = self.provider.text_translate("中路来抓一下上路", target_lang="en")
        self.assertEqual(result["status"], "success")
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
        self.assertIsInstance(payload["messages"][-1]["content"], str)


class TestConnectionError(unittest.TestCase):
    @mock.patch("lolchattranslator.providers.openai_compat.requests.Session.post")
    def test_timeout(self, mock_post):
        import requests

        mock_post.side_effect = requests.exceptions.ConnectTimeout()
        provider = OpenAICompatProvider(CONFIG, "sk-test")
        with self.assertRaises(ProviderError) as ctx:
            provider.chat([{"role": "user", "content": "hi"}])
        self.assertEqual(ctx.exception.category, "timeout")


if __name__ == "__main__":
    unittest.main()

"""核心数据模型与翻译服务测试。"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from lolchattranslator.core.models import TaskKind, TranslationRequest, TranslationResult  # noqa: E402
from lolchattranslator.core.translation_service import TranslationService  # noqa: E402
from lolchattranslator.infrastructure.config_store import ConfigStore  # noqa: E402
from lolchattranslator.providers import get_provider  # noqa: E402


class TestModels(unittest.TestCase):
    def test_task_kind_values(self):
        self.assertEqual(TaskKind.IMAGE.value, "image")
        self.assertEqual(TaskKind.REPLY.value, "reply")

    def test_result_ok(self):
        r = TranslationResult(translated="hi")
        self.assertTrue(r.ok)
        r2 = TranslationResult(status="error", error="boom")
        self.assertFalse(r2.ok)


class TestTranslationService(unittest.TestCase):
    def _make_service(self, tmpdir):
        cfg = ConfigStore(config_path=Path(tmpdir) / "config.json")
        cfg.set("api.provider", "deepseek")
        svc = TranslationService(cfg)
        svc.secret_store = mock.Mock()
        return cfg, svc

    def test_missing_key_raises_auth(self):
        with tempfile.TemporaryDirectory() as d:
            cfg, svc = self._make_service(d)
            svc.secret_store.get_key.return_value = ""
            req = TranslationRequest(kind=TaskKind.REPLY, text="你好", target_lang="en")
            result = svc.translate_text(req)
            self.assertEqual(result.status, "error")
            self.assertEqual(result.error_category, "auth")

    def test_get_provider_all_names(self):
        for name in ["deepseek", "gpt", "gemini", "grok", "kimi", "ollama", "openai_compat"]:
            self.assertTrue(callable(get_provider(name)))

    def test_unknown_provider_raises(self):
        from lolchattranslator.providers import ProviderError  # noqa: F401

        with self.assertRaises(ValueError):
            get_provider("nonexistent")


if __name__ == "__main__":
    unittest.main()

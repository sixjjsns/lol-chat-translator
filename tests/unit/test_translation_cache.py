"""截图翻译缓存键测试：目标语言/温度变化后不得命中旧缓存。"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from lolchattranslator.core.translation_service import TranslationService  # noqa: E402


class TestCacheKey(unittest.TestCase):
    def setUp(self):
        self.svc = TranslationService.__new__(TranslationService)  # 不需要 ConfigStore

    def test_same_inputs_same_key(self):
        a = self.svc._cache_key("data:image/jpeg;base64,AAAA", "zh", 0.7)
        b = self.svc._cache_key("data:image/jpeg;base64,AAAA", "zh", 0.7)
        self.assertEqual(a, b)

    def test_target_lang_changes_key(self):
        zh = self.svc._cache_key("data:image/jpeg;base64,AAAA", "zh", 0.7)
        en = self.svc._cache_key("data:image/jpeg;base64,AAAA", "en", 0.7)
        self.assertNotEqual(zh, en)

    def test_temperature_changes_key(self):
        low = self.svc._cache_key("data:image/jpeg;base64,AAAA", "zh", 0.2)
        high = self.svc._cache_key("data:image/jpeg;base64,AAAA", "zh", 0.9)
        self.assertNotEqual(low, high)

    def test_image_changes_key(self):
        a = self.svc._cache_key("data:image/jpeg;base64,AAAA", "zh", 0.7)
        b = self.svc._cache_key("data:image/jpeg;base64,BBBB", "zh", 0.7)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()

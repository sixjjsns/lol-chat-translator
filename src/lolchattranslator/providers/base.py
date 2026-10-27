"""Provider 抽象基类与协议定义。"""
from abc import ABC, abstractmethod


class ProviderError(Exception):
    """带错误分类的异常。"""

    def __init__(self, message: str, category: str = "unknown"):
        super().__init__(message)
        self.message = message
        self.category = category  # auth / model_unavailable / quota / timeout / server / network / unknown


class BaseProvider(ABC):
    """所有翻译 Provider 的统一协议。"""

    name = "base"

    @abstractmethod
    def __init__(self, config: dict, api_key: str):
        ...

    @abstractmethod
    def vision_translate(self, image_data_url: str, prompt: str,
                         source_lang: str = "auto", target_lang: str = "zh") -> dict:
        """发送带图片的翻译请求，返回标准化结构 {raw, status, model, usage}。"""

    @abstractmethod
    def text_translate(self, text: str, target_lang: str = "en") -> dict:
        """纯文本翻译（用于用户输入中文回复给对方）。"""

    @abstractmethod
    def test_connection(self) -> dict:
        """连接测试。"""

    def set_temperature(self, temperature: float):
        """动态调节 temperature（人性化程度）。"""
        raise NotImplementedError

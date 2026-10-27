"""Provider 注册表与能力声明。

所有云服务（DeepSeek / GPT / Gemini / Grok / Kimi）和本地 Ollama
都走 OpenAI 兼容 Chat Completions 格式，统一使用 OpenAICompatProvider，
区别仅在于 base_url 和 model。具体服务模板见 config/default_config.json。
"""
from .base import BaseProvider, ProviderError
from .openai_compat import OpenAICompatProvider

# 供应商注册表：名字 -> Provider 类
PROVIDERS = {
    "openai_compat": OpenAICompatProvider,
    "deepseek": OpenAICompatProvider,
    "gpt": OpenAICompatProvider,
    "gemini": OpenAICompatProvider,
    "grok": OpenAICompatProvider,
    "kimi": OpenAICompatProvider,
    "zhipu": OpenAICompatProvider,
    "ollama": OpenAICompatProvider,
}


def get_provider(name: str):
    if name not in PROVIDERS:
        raise ValueError(f"未知的 API 供应商: {name}，可用: {list(PROVIDERS.keys())}")
    return PROVIDERS[name]


def available_providers() -> list:
    return list(PROVIDERS.keys())


__all__ = [
    "BaseProvider",
    "ProviderError",
    "OpenAICompatProvider",
    "get_provider",
    "available_providers",
    "PROVIDERS",
]

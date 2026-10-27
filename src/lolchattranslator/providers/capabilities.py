"""Provider 能力声明。

不同服务对 vision / temperature 等参数的支持可能不同。
此模块用于在运行时查询 Provider 的能力，避免对所有模型强制传递相同参数。
"""
from dataclasses import dataclass, field


@dataclass
class ProviderCapabilities:
    supports_vision: bool = True
    supports_temperature: bool = True
    requires_api_key: bool = True
    extra: dict = field(default_factory=dict)


# 各服务默认能力（OpenAI 兼容协议下大部分能力一致，主要差异在 requires_api_key）
CAPABILITIES = {
    "deepseek": ProviderCapabilities(),
    "gpt": ProviderCapabilities(),
    "gemini": ProviderCapabilities(),
    "grok": ProviderCapabilities(),
    "kimi": ProviderCapabilities(),
    "ollama": ProviderCapabilities(requires_api_key=False),
    "openai_compat": ProviderCapabilities(),
}


def get_capabilities(provider_name: str) -> ProviderCapabilities:
    return CAPABILITIES.get(provider_name, ProviderCapabilities())

"""核心数据模型：翻译请求、翻译结果、任务状态。"""
from dataclasses import dataclass
from enum import StrEnum


class TaskKind(StrEnum):
    IMAGE = "image"       # 截图翻译
    REPLY = "reply"       # 文本反向翻译


@dataclass
class TranslationRequest:
    """统一的翻译请求模型。"""
    kind: TaskKind
    # image 任务：截图 PNG 字节；reply 任务：用户输入文本
    image_bytes: bytes | None = None
    text: str | None = None
    target_lang: str = "zh"
    source_lang: str = "auto"
    temperature: float | None = None
    force: bool = False  # 忽略缓存强制重新翻译


@dataclass
class TranslationResult:
    """统一的翻译结果模型。"""
    kind: TaskKind = TaskKind.IMAGE
    translated: str = ""
    status: str = "success"
    model: str = ""
    detected_lang: str = "auto"
    img_ms: float = 0.0
    api_ms: float = 0.0
    total_ms: float = 0.0
    cached: bool = False
    error: str | None = None
    error_category: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "success" and self.error is None


@dataclass
class TaskState:
    """后台任务状态（用于 UI 展示与取消）。"""
    kind: TaskKind
    request: TranslationRequest
    result: TranslationResult | None = None
    cancelled: bool = False

"""翻译服务：协调 Provider、缓存、去重、术语表，线程安全。"""
import hashlib
import threading
import time

from ..infrastructure.config_store import ConfigStore
from ..infrastructure.logging_config import get_logger
from ..infrastructure.secret_store import SecretStore
from ..providers import get_provider
from ..providers.base import ProviderError
from ..services.image_processor import ImageProcessor
from .models import TaskKind, TranslationRequest, TranslationResult

logger = get_logger()


class TranslationService:
    def __init__(self, config: ConfigStore):
        self.config = config
        self.secret_store = SecretStore()
        self._provider = None
        self._cache = {}  # key -> (timestamp, result)
        self._lock = threading.Lock()
        self._last_result: TranslationResult | None = None

    def _get_provider(self):
        cfg = self.config.get("api", {})
        api_key = self.secret_store.get_key()
        provider_name = cfg.get("provider", "deepseek")
        # Ollama 本地模型不需要 API Key
        if provider_name != "ollama" and not api_key:
            raise ProviderError("未配置 API Key，请先打开设置配置", "auth")
        provider_cls = get_provider(provider_name)
        return provider_cls(cfg, api_key or "")

    def _cache_key(self, image_data_url: str) -> str:
        return hashlib.sha256(image_data_url.encode("utf-8")).hexdigest()

    def _build_prompt(self) -> str:
        glossary = self.config.get("glossary", {}) or {}
        lines = ["请识别截图中的游戏聊天内容并翻译。"]
        if glossary:
            term_lines = [f"{k} -> {v}" for k, v in glossary.items()]
            lines.append("术语表（请优先采用这些翻译）：" + "；".join(term_lines))
        return "\n".join(lines)

    def translate(self, request: TranslationRequest) -> TranslationResult:
        """统一入口：根据任务类型分发到截图翻译或文本翻译。"""
        if request.kind == TaskKind.IMAGE:
            return self.translate_image(request)
        return self.translate_text(request)

    def translate_image(self, request: TranslationRequest) -> TranslationResult:
        """主流程：图像 -> 压缩 -> 缓存/去重 -> 调用 Provider -> 结构化结果。"""
        t_start = time.perf_counter()
        png_bytes = request.image_bytes
        cfg_capture = self.config.get("capture", {})
        processor = ImageProcessor(
            max_dimension=cfg_capture.get("max_dimension", 1600),
            jpeg_quality=cfg_capture.get("jpeg_quality", 85),
        )
        t_img_start = time.perf_counter()
        data_url = processor.process(png_bytes)
        t_img = (time.perf_counter() - t_img_start) * 1000

        # 有界缓存（相同截图去重），force=True 时跳过
        cfg_behav = self.config.get("behavior", {})
        if cfg_behav.get("cache_enabled", True) and not request.force:
            key = self._cache_key(data_url)
            with self._lock:
                hit = self._cache.get(key)
                if hit:
                    ts, result = hit
                    ttl = cfg_behav.get("cache_ttl_seconds", 60)
                    if time.time() - ts < ttl:
                        result = dict(result)
                        if isinstance(result.get("kind"), str):
                            result["kind"] = TaskKind(result["kind"])
                        result = TranslationResult(**result)
                        result.cached = True
                        result.total_ms = (time.perf_counter() - t_start) * 1000
                        logger.info("命中缓存，跳过重复请求（总耗时 %.1fms）", result.total_ms)
                        return result
        prompt = self._build_prompt()
        try:
            provider = self._get_provider()
        except ProviderError as e:
            return self._error_result(e)

        if request.temperature is not None:
            provider.set_temperature(request.temperature)

        t_api_start = time.perf_counter()
        try:
            raw = provider.vision_translate(data_url, prompt, request.source_lang, request.target_lang)
        except ProviderError as e:
            return self._error_result(e)
        t_api = (time.perf_counter() - t_api_start) * 1000

        result = TranslationResult(
            kind=TaskKind.IMAGE,
            translated=raw["raw"].strip(),
            status=raw["status"],
            model=raw.get("model", ""),
            detected_lang=request.source_lang,
            img_ms=round(t_img, 1),
            api_ms=round(t_api, 1),
            total_ms=round((time.perf_counter() - t_start) * 1000, 1),
            cached=False,
        )

        # 缓存
        if cfg_behav.get("cache_enabled", True):
            with self._lock:
                self._trim_cache()
                self._cache[self._cache_key(data_url)] = (
                    time.time(),
                    self._result_to_dict(result),
                )

        logger.info(
            "截图翻译完成：图片处理 %.1fms / API 调用 %.1fms / 总耗时 %.1fms（模型=%s）",
            result.img_ms,
            result.api_ms,
            result.total_ms,
            result.model or "-",
        )
        self._last_result = result
        return result

    def translate_text(self, request: TranslationRequest) -> TranslationResult:
        """纯文本翻译：用户输入中文 -> 目标语言（用于游戏内回复）。"""
        t_start = time.perf_counter()
        try:
            provider = self._get_provider()
        except ProviderError as e:
            return self._error_result(e)

        if request.temperature is not None:
            provider.set_temperature(request.temperature)

        t_api_start = time.perf_counter()
        try:
            raw = provider.text_translate(request.text, request.target_lang)
        except ProviderError as e:
            return self._error_result(e)
        t_api = (time.perf_counter() - t_api_start) * 1000

        result = TranslationResult(
            kind=TaskKind.REPLY,
            translated=raw["raw"],
            status=raw["status"],
            model=raw.get("model", ""),
            api_ms=round(t_api, 1),
            total_ms=round((time.perf_counter() - t_start) * 1000, 1),
        )
        logger.info(
            "文本翻译完成：API 调用 %.1fms / 总耗时 %.1fms（模型=%s）",
            result.api_ms,
            result.total_ms,
            result.model or "-",
        )
        self._last_result = result
        return result

    def test_connection(self) -> dict:
        try:
            provider = self._get_provider()
        except ProviderError as e:
            return {"ok": False, "category": e.category, "error": e.message}
        try:
            return provider.test_connection()
        except ProviderError as e:
            return {"ok": False, "category": e.category, "error": e.message}

    def get_last_result(self) -> TranslationResult | None:
        return self._last_result

    # --- 内部 ---
    @staticmethod
    def _error_result(e: ProviderError) -> TranslationResult:
        return TranslationResult(
            kind=TaskKind.IMAGE,
            status="error",
            error=e.message,
            error_category=e.category,
        )

    @staticmethod
    def _result_to_dict(result: TranslationResult) -> dict:
        return {
            "kind": result.kind.value,
            "translated": result.translated,
            "status": result.status,
            "model": result.model,
            "detected_lang": result.detected_lang,
            "img_ms": result.img_ms,
            "api_ms": result.api_ms,
            "total_ms": result.total_ms,
            "cached": result.cached,
            "error": result.error,
            "error_category": result.error_category,
        }

    def _trim_cache(self, max_entries: int = 50):
        if len(self._cache) > max_entries:
            items = sorted(self._cache.items(), key=lambda kv: kv[1][0])
            for k, _ in items[: len(self._cache) - max_entries]:
                del self._cache[k]

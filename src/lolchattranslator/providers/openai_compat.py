"""通用 OpenAI 兼容 Provider：支持视觉（image_url + Base64）。

通过不同的 base_url + 模型名，支持 DeepSeek / GPT / Gemini / Grok / Kimi / Ollama 等
所有走 OpenAI 兼容 Chat Completions 格式的服务。

各服务默认配置见 config/default_config.json 的 providers 段。

v1.2.2 翻译可靠性改造
-------------------
- Prompt 统一由 `providers/prompts.py` 生成：角色固定为"翻译引擎"，
  待翻译文本用 `<<< >>>` 包裹，并明确"即使是问句/命令也只翻译不回答"。
- 输出统一走 `sanitize_translation()`：去掉"翻译：""以下是"、引号、代码块等包装。
- `looks_like_non_translation()` 判断模型是否在"回答"，命中则用严格模式
  （超短 prompt + 0.2 温度）**自动重试一次**，可用 `api.strict_translate=false` 关闭。
- 翻译温度上限 0.6，避免高温导致发散和胡编。
"""

import requests

from ..infrastructure.logging_config import get_logger
from . import prompts
from .base import BaseProvider, ProviderError

logger = get_logger()

# 翻译场景下温度上限（"人性化"滑块再高也不超过这个值，防止模型发散）
MAX_TRANSLATE_TEMPERATURE = 0.6
# 严格重试时的温度
STRICT_TEMPERATURE = 0.2
# 反向翻译（一两句回复）最多生成的 token 数
REPLY_MAX_TOKENS = 300


class OpenAICompatProvider(BaseProvider):
    """OpenAI 兼容 Provider，可指向任意服务。"""

    name = "openai_compat"

    def __init__(self, config: dict, api_key: str):
        self.base_url = config.get("base_url", "https://api.deepseek.com").rstrip("/")
        self.model = config.get("model", "deepseek-flash")
        self.timeout_connect = config.get("timeout_connect", 10)
        self.timeout_read = config.get("timeout_read", 30)
        self.max_tokens = config.get("max_tokens", 512)
        self.temperature = config.get("temperature", 0.7)
        self.image_detail = config.get("image_detail", "high")
        self.strict_translate = bool(config.get("strict_translate", True))
        self.api_key = api_key
        self._session = requests.Session()

    def _endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def set_temperature(self, temperature: float):
        self.temperature = temperature

    def _classify_error(self, status: int, body: str) -> ProviderError:
        low = (body or "").lower()
        if status == 401:
            return ProviderError("认证失败：API Key 无效", "auth")
        if status == 403:
            return ProviderError("无权限访问该模型", "auth")
        if status == 404:
            return ProviderError("模型不存在或端点错误", "model_unavailable")
        if status == 429:
            return ProviderError("请求过于频繁或额度不足（429）", "quota")
        if status >= 500:
            return ProviderError(f"服务端错误（HTTP {status}）", "server")
        if status == 400 and "not support image" in low:
            return ProviderError("当前模型不支持图像输入，请更换支持识图的模型", "model_unavailable")
        if status == 400 and ("insufficient" in low or "balance" in low or "quota" in low):
            return ProviderError("账户余额不足或额度用尽", "quota")
        return ProviderError(f"请求失败（HTTP {status}）: {body[:200]}", "unknown")

    def chat(self, messages: list[dict], timeout_connect: int | None = None,
             timeout_read: int | None = None, temperature: float | None = None,
             max_tokens: int | None = None) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": self.temperature if temperature is None else temperature,
            "stream": False,
        }
        try:
            resp = self._session.post(
                self._endpoint(),
                headers=self._headers(),
                json=payload,
                timeout=(timeout_connect or self.timeout_connect, timeout_read or self.timeout_read),
            )
        except requests.exceptions.ConnectTimeout:
            raise ProviderError("连接超时", "timeout") from None
        except requests.exceptions.ReadTimeout:
            raise ProviderError("读取超时（服务端响应过慢）", "timeout") from None
        except requests.exceptions.ConnectionError as e:
            raise ProviderError(f"网络连接失败: {e}", "network") from e
        except requests.exceptions.RequestException as e:
            raise ProviderError(f"网络请求异常: {e}", "network") from e

        if resp.status_code != 200:
            raise self._classify_error(resp.status_code, resp.text)

        try:
            data = resp.json()
        except Exception:
            raise ProviderError("响应不是有效 JSON", "server") from None

        return data

    # ------------------------------------------------------------------
    # 内部工具
    # ------------------------------------------------------------------
    def _translate_temperature(self) -> float:
        return max(0.0, min(float(self.temperature or 0.0), MAX_TRANSLATE_TEMPERATURE))

    @staticmethod
    def _extract_content(data: dict) -> str:
        """从响应里取文字，兼容 content 为 None / list（多模态）的情况。"""
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ProviderError("响应结构异常，缺少 choices", "server") from None
        if content is None:
            return ""
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item, str):
                    parts.append(item)
            return "".join(parts)
        return str(content)

    # ------------------------------------------------------------------
    # 视觉翻译（截图 → 译文）
    # ------------------------------------------------------------------
    def vision_translate(self, image_data_url: str, prompt: str,
                         source_lang: str = "auto", target_lang: str = "zh") -> dict:
        """发送带图片的翻译请求，返回标准化结构。"""
        raw, model = self._vision_once(image_data_url, prompt, target_lang, strict=False)
        text = prompts.sanitize_translation(raw, target_lang)

        if self.strict_translate and prompts.looks_like_non_translation("", text, target_lang):
            logger.warning("视觉翻译疑似在回答问题，改用严格模式重试：%r", text[:60])
            retry_raw, retry_model = self._vision_once(image_data_url, prompt, target_lang, strict=True)
            retry_text = prompts.sanitize_translation(retry_raw, target_lang)
            if retry_text:
                model = retry_model
            if retry_text and not prompts.looks_like_non_translation("", retry_text, target_lang):
                text = retry_text

        if not text:
            logger.warning("视觉翻译返回空内容：模型未识别到聊天文字（截图可能无文字或模型拒答）")
        else:
            logger.info("视觉翻译返回内容长度=%d", len(text))

        return {
            "raw": text,
            "status": "success",
            "model": model,
            "usage": None,
        }

    def _vision_once(self, image_data_url: str, extra_prompt: str,
                     target_lang: str, strict: bool) -> tuple[str, str]:
        system = (
            prompts.build_strict_system_prompt(target_lang)
            if strict
            else prompts.build_vision_system_prompt(target_lang)
        )
        user_text = "翻译这张截图里的游戏聊天内容，只输出译文。"
        extra = (extra_prompt or "").replace("请识别截图中的游戏聊天内容并翻译。", "").strip()
        if extra:
            user_text += "\n" + extra

        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url, "detail": self.image_detail},
                    },
                ],
            },
        ]
        temperature = STRICT_TEMPERATURE if strict else self._translate_temperature()
        data = self.chat(messages, temperature=temperature)
        return self._extract_content(data), data.get("model", self.model)

    # ------------------------------------------------------------------
    # 文本翻译（中文 → 目标语言）
    # ------------------------------------------------------------------
    def text_translate(self, text: str, target_lang: str = "en") -> dict:
        """纯文本翻译（用于用户输入中文回复给对方）。"""
        source = (text or "").strip()
        raw, model = self._text_once(source, target_lang, strict=False)
        clean = prompts.sanitize_translation(raw, target_lang)

        if self.strict_translate and prompts.looks_like_non_translation(source, clean, target_lang):
            logger.warning("文本翻译疑似在回答而不是翻译，改用严格模式重试：%r", clean[:60])
            retry_raw, retry_model = self._text_once(source, target_lang, strict=True)
            retry_clean = prompts.sanitize_translation(retry_raw, target_lang)
            if retry_clean and not prompts.looks_like_non_translation(source, retry_clean, target_lang):
                clean = retry_clean
                model = retry_model

        if not clean:
            logger.warning("文本翻译返回空内容（输入：%r）", source[:40])

        return {
            "raw": clean,
            "status": "success",
            "model": model,
            "usage": None,
        }

    def _text_once(self, text: str, target_lang: str, strict: bool) -> tuple[str, str]:
        system = (
            prompts.build_strict_system_prompt(target_lang)
            if strict
            else prompts.build_reply_system_prompt(target_lang)
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompts.wrap_user_text(text)},
        ]
        temperature = STRICT_TEMPERATURE if strict else self._translate_temperature()
        max_tokens = min(self.max_tokens, REPLY_MAX_TOKENS)
        data = self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        return self._extract_content(data), data.get("model", self.model)

    def test_connection(self) -> dict:
        """连接测试：用一条纯文本消息验证认证与模型可用性。"""
        messages = [{"role": "user", "content": "ping"}]
        data = self.chat(messages, timeout_connect=8, timeout_read=15)
        try:
            reply = self._extract_content(data)
        except ProviderError:
            reply = ""
        return {"ok": True, "model": data.get("model", self.model), "reply": reply[:50]}

    # ------------------------------------------------------------------
    # 兼容旧接口（外部可能引用静态 prompt 方法）
    # ------------------------------------------------------------------
    @staticmethod
    def _system_prompt(target_lang: str) -> str:
        return prompts.build_vision_system_prompt(target_lang)

    @staticmethod
    def _reply_system_prompt(target_lang: str) -> str:
        return prompts.build_reply_system_prompt(target_lang)

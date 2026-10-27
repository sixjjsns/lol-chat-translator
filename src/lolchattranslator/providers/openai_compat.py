"""通用 OpenAI 兼容 Provider：支持视觉（image_url + Base64）。

通过不同的 base_url + 模型名，支持 DeepSeek / GPT / Gemini / Grok / Kimi / Ollama 等
所有走 OpenAI 兼容 Chat Completions 格式的服务。

各服务默认配置见 config/default_config.json 的 providers 段。
"""

import requests

from ..infrastructure.logging_config import get_logger
from .base import BaseProvider, ProviderError

logger = get_logger()


class OpenAICompatProvider(BaseProvider):
    """OpenAI 兼容 Provider，可指向任意服务。"""

    name = "openai_compat"

    def __init__(self, config: dict, api_key: str):
        self.base_url = config.get("base_url", "https://api.deepseek.com").rstrip("/")
        self.model = config.get("model", "deepseek-flash")
        self.timeout_connect = config.get("timeout_connect", 10)
        self.timeout_read = config.get("timeout_read", 30)
        self.max_tokens = config.get("max_tokens", 2048)
        self.temperature = config.get("temperature", 0.7)
        self.image_detail = config.get("image_detail", "low")
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
             timeout_read: int | None = None) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
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

    def vision_translate(self, image_data_url: str, prompt: str,
                         source_lang: str = "auto", target_lang: str = "zh") -> dict:
        """发送带图片的翻译请求，返回标准化结构。"""
        messages = [
            {"role": "system", "content": self._system_prompt(target_lang)},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url, "detail": self.image_detail}},
                ],
            },
        ]
        data = self.chat(messages)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise ProviderError("响应结构异常，缺少 choices", "server") from None
        return {
            "raw": content,
            "status": "success",
            "model": data.get("model", self.model),
            "usage": data.get("usage"),
        }

    def text_translate(self, text: str, target_lang: str = "en") -> dict:
        """纯文本翻译（用于用户输入中文回复给对方）。"""
        messages = [
            {"role": "system", "content": self._reply_system_prompt(target_lang)},
            {"role": "user", "content": text},
        ]
        data = self.chat(messages)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise ProviderError("响应结构异常，缺少 choices", "server") from None
        return {
            "raw": content.strip(),
            "status": "success",
            "model": data.get("model", self.model),
            "usage": data.get("usage"),
        }

    def test_connection(self) -> dict:
        """连接测试：用一条纯文本消息验证认证与模型可用性。"""
        messages = [{"role": "user", "content": "ping"}]
        data = self.chat(messages, timeout_connect=8, timeout_read=15)
        try:
            reply = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            reply = ""
        return {"ok": True, "model": data.get("model", self.model), "reply": reply[:50]}

    @staticmethod
    def _system_prompt(target_lang: str) -> str:
        lang_name = {"zh": "简体中文", "en": "英文", "ja": "日文", "ko": "韩文"}.get(target_lang, target_lang)
        return (
            f"你是英雄联盟游戏聊天翻译助手。把截图里的外语聊天翻译成{lang_name}，让玩家能立刻看懂对方在说什么。\n\n"
            "核心要求（最重要）：\n"
            "1. 【意译优先，禁止机翻】翻译出对方真正想表达的意思，而不是逐字直译。\n"
            "   - 错误机翻：「你在哪里死掉了」\n"
            "   - 正确自然：「你咋死了」「你在哪死的」\n"
            "   - 要像真人玩家之间聊天那样自然、口语化、接地气。\n"
            "2. 【口语化】用游戏玩家日常的说法，可以带语气词（了、啊、吧、呗、吗），但不要过度。\n"
            "3. 【保留专有名词】英雄名、技能名、装备名、游戏术语（gg、wp、afk、mid、top、gank、dragon、baron 等）保持原样或按国内玩家习惯叫法，不翻译。\n"
            "4. 【保留语气】否定、反讽、嘲讽、调侃、求助、指挥等语气要翻出来，不要翻成平淡的陈述句。\n"
            "5. 【忠实】对无法辨认的文字标记[不确定]，绝不编造、不脑补没说的话。\n"
            "6. 【只输出译文】不要加解释、不要加引号、不要讲解。\n"
            "7. 【逐条】如果截图有多条消息，按顺序逐条翻译，不同玩家的话不要合并成一条。"
        )

    @staticmethod
    def _reply_system_prompt(target_lang: str) -> str:
        lang_name = {"zh": "简体中文", "en": "英文", "ja": "日文", "ko": "韩文"}.get(target_lang, target_lang)
        return (
            "你是英雄联盟游戏聊天翻译助手。把用户输入的中文翻译成" + lang_name + "，用于在游戏内回复队友或嘲讽对手。\n\n"
            "核心要求（最重要）：\n"
            "1. 【地道口语，禁止机翻】翻译成" + lang_name + "母语玩家真正会打出来的话，不要中式英语、不要逐字硬译。\n"
            "   - 错误机翻（中式英语）：\"you are very vegetable\"（你很菜）\n"
            "   - 正确地道：\"you're so bad\" / \"nice feed\" / \"uninstall\"\n"
            "   - 要符合" + lang_name + "玩家真实的聊天习惯和俚语。\n"
            "2. 【保留游戏术语】英雄名、技能名、装备名、以及 gg、wp、afk、mid、top、gank、diff 等术语按游戏惯例处理，不硬翻。\n"
            "3. 【保留情绪】调侃、反击、嘲讽、鼓励、指挥等情绪要自然流露，符合游戏氛围。\n"
            "4. 【简短有力】游戏聊天通常一两句话，不要啰嗦、不要写作文。\n"
            "5. 【只输出翻译结果】不要加引号、解释、前缀（如\"翻译：\"）。"
        )

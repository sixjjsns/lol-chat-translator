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
        self.max_tokens = config.get("max_tokens", 512)
        self.temperature = config.get("temperature", 0.7)
        self.image_detail = config.get("image_detail", "high")
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

        # 健壮性：部分视觉模型 content 可能是 None、空串、或列表（多模态结构）
        if content is None:
            content = ""
        if isinstance(content, list):
            # 多模态 content 数组：拼接所有 text 片段
            parts = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item, str):
                    parts.append(item)
            content = "".join(parts)

        text = str(content).strip()
        if not text:
            logger.warning("视觉翻译返回空内容：模型未识别到聊天文字（截图可能无文字或模型拒答）")
        else:
            logger.info("视觉翻译返回内容长度=%d", len(text))

        return {
            "raw": text,
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
            f"你是英雄联盟国际服玩家之间的聊天翻译助手。把截图里队友发的消息翻译成{lang_name},"
            "让玩家能立刻看懂对方在说什么——要像真人在打游戏时打出来的话,不是机翻。\n\n"
            "【英雄联盟术语词典(翻译时保留原样或按国内玩家习惯,不要硬翻)】\n"
            "位置:top(上单)、mid(中单)、jg/jungle(打野)、adc/bot(下路)、sup(辅助)\n"
            "技能:ult/ultimate(大招)、cc(控制)、q/w/e/r(技能键)、smite(惩戒)、flash(闪现)、ignite(点燃)\n"
            "资源:baron(大龙)、dragon/drake(小龙)、herald(先锋)、buff(增益)、blue/red(蓝/红 buff)、scuttle(河蟹)、tower/turret(塔)、inhib(水晶兵营)、nexus(基地)\n"
            "战术:gank(抓人)、push(推)、defend(守)、split(分带)、roam(游走)、back/recall(回城)、ward(插眼)、group(集合)、engage(开团)、peel(保排)、kite(风筝)、focus(集火)、ss/mia(失踪)、re(回来了)、omw(在路上)、oom(没蓝)\n"
            "情绪/俚语:gg、wp(well played)、gj/nice(打得好)、mb(my bad我的错)、glhf(开局问好)、nr(need report)、diff(差距:mid diff)、noob/feeder(菜/送)、afk(挂机)、ks(抢人头)、int(故意送/摆烂)、ez(嘲讽)、report(举报)、spam(刷屏)、xd、lol、rofl、zzzzz(韩)、wwwww(日)、ㅋㅋㅋ(韩笑)\n\n"
            "【翻译核心要求】\n"
            "1. 【真人语气,禁止机翻】把对方真正想表达的意思翻出来,不是逐字直译。\n"
            "   - 例:对方打'where mid gank?' 应翻成'中单去哪了 不来抓吗' 而不是'中单去哪里了抓'\n"
            "   - 例:对方打'jg diff' 应翻成'打野差距/打野太菜了' 而不是'打野差异'\n"
            "   - 要像玩家实时打字,口语化、接地气、带语气词(了、啊、吧、吗、呢)。\n"
            "2. 【情绪保留】嘲讽、求救、指挥、抱怨、调侃、鼓励、骂人这些语气都要翻出来,不要翻成平淡陈述。\n"
            "   - 例:'gg ez' → '打得好 轻松拿下'(保留嘲讽)\n"
            "   - 例:'jg where???' → '打野人呢???'(保留急躁)\n"
            "   - 例:'mb sry' → '我的 错了'(保留歉意)\n"
            "3. 【术语处理】上面的 LoL 术语要么保留英文(gg/gank/baron/ult),要么用国内玩家习惯叫法(大龙/抓人/大招),不要硬翻成生硬词组。\n"
            "4. 【简短】玩家聊天通常 1-2 句,不要扩充解释、不要加引号、不要加'翻译:'前缀。\n"
            "5. 【忠实,不脑补】对看不清/识别不出的部分标记[不确定],绝不编造对方没说的话。\n"
            "6. 【逐条】截图有多条消息按顺序逐条翻译,不同玩家的话分开,不要合并成一句。\n"
            "7. 【缩写/俚语识别】ss/mia=失踪,re=回来了,omw=在路上,oom=没蓝,这些要按意思翻而不是按字母翻。\n"
        )

    @staticmethod
    def _reply_system_prompt(target_lang: str) -> str:
        lang_name = {"zh": "简体中文", "en": "英文", "ja": "日文", "ko": "韩文"}.get(target_lang, target_lang)
        return (
            "你是英雄联盟国际服玩家之间的聊天翻译助手。把用户输入的中文翻译成" + lang_name + ",用于在游戏内回复队友或嘲讽对手。"
            "翻译结果必须像" + lang_name + "母语玩家真正会打出来的话——不要中式外语、不要逐字硬译。\n\n"
            "【英雄联盟术语词典(翻译时保留原样,不要硬翻)】\n"
            "位置:top/mid/jg/adc/bot/sup\n"
            "技能:ult(大招)、cc、smite、flash、ignite、q/w/e/r\n"
            "资源:baron、dragon/drake、herald、buff、tower/turret、inhib、nexus、scuttle\n"
            "战术:gank、push、defend、split、roam、back/recall、ward、group、engage、peel、kite、focus、ss/mia、re、omw、oom\n"
            "俚语:gg、wp、gj、mb(my bad)、glhf、diff、noob、feeder、afk、ks、int、ez、report、xd、lol、rofl\n"
            "韩语特有笑:ㅋㅋㅋ/kkkkk;日语特有笑:wwww/www;英语:lol/rofl/lmao\n\n"
            "【翻译核心要求】\n"
            "1. 【地道,禁止中式外语】翻成" + lang_name + "玩家真实打字习惯的俚语和句式,不要逐字翻译。\n"
            "   - 错误(中式英语):'you are very vegetable'(你很菜) → 正确:'you're so bad' / 'nice feed' / 'uninstall'\n"
            "   - 错误(中式日语):'あなたはとても野菜です' → 正确:'お前杂鱼すぎ' / '上手すぎ'\n"
            "   - 错误(中式韩语):'너는 매우 야채다' → 正确:'개못함' / ' uninstall'\n"
            "2. 【保留游戏术语】gg/wp/afk/mid/top/gank/diff/ult/baron/dragon 这些不要硬翻,按当地玩家习惯处理。\n"
            "3. 【保留情绪】调侃、嘲讽、反击、鼓励、指挥、求救这些情绪都要自然流露,符合国际服游戏氛围。\n"
            "   - 例:中文'你太菜了' → 英文'you're so bad' / 日文'下手すぎ' / 韩文'개못함'\n"
            "   - 例:中文'打野差距' → 英文'jg diff' / 日文'jg diff' / 韩文'jg diff'\n"
            "   - 例:中文'别送了' → 英文'stop feeding' / 日文'フィードすんな' / 韩文'빠져라'\n"
            "4. 【简短有力】游戏聊天 1-2 句,不要啰嗦、不要写作文、不要加'翻译:'前缀、不要加引号。\n"
            "5. 【该用俚语就用俚语】" + lang_name + "玩家间有约定俗成的游戏俚语,直接用,不要绕弯子翻译。\n"
            "6. 【缩写优先】能缩写就缩写(ult 不写 ultimate、jg 不写 jungle、wp 不写 well played),符合实战打字速度。\n"
        )

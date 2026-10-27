"""国际化（i18n）：界面语言中英切换。

使用简单的字典 + 全局当前语言，避免引入重型 i18n 框架。
UI 层通过 tr(key) 取文案，切换语言后调用刷新。
"""

# 当前界面语言：zh / en
_current_lang = "zh"

# 文案字典
MESSAGES = {
    "zh": {
        "app.title": "LoL Chat Translator",
        "app.brand": "LoL 翻译",
        "nav.translate": "🖥  翻译",
        "nav.settings": "⚙  设置",
        "status.ready": "就绪 · 按 F6 截图翻译",
        # 翻译页
        "btn.capture": "📷 截取翻译",
        "btn.select_region": "选择区域",
        "label.output_lang": "输出语言",
        "label.naturalness": "翻译人性化程度",
        "label.literal": "直译",
        "label.colloquial": "口语化",
        "label.result": "译文",
        "label.reply": "回复对方（输入中文，翻译成对方语言）",
        "placeholder.result": "译文将显示在这里…\n\n按 F6 截取聊天区域翻译，或输入下方文字反向翻译。",
        "placeholder.reply": "例如：来中路抓一下，谢谢",
        "btn.reply": "翻译并复制",
        "hint.reply_empty": "请先输入要翻译的内容",
        "hint.reply_ing": "翻译中…",
        "hint.reply_done": "已翻译并复制到剪贴板",
        # 设置页
        "settings.title": "设置",
        "settings.tab.provider": "翻译服务",
        "settings.tab.language": "语言",
        "settings.tab.hotkey": "快捷键",
        "settings.provider": "翻译服务：",
        "settings.api_key": "API Key：",
        "settings.base_url": "Base URL：",
        "settings.model": "模型：",
        "settings.model_hint": "模型须支持识图/图像输入",
        "settings.test": "测试连接",
        "settings.source_lang": "源语言：",
        "settings.target_lang": "截图翻译目标语言：",
        "settings.lang_hint": "源语言默认「自动识别」，无需手动设置。",
        "settings.reset_hotkey": "恢复默认快捷键",
        "settings.hotkey_hint": "可用键：f1-f12、home、end、insert、delete、page up/down、ctrl+alt+字母",
        "settings.clear_key": "清除 Key",
        "settings.save": "保存",
        "settings.warn_key_required": "API Key 不能为空（本地 Ollama 无需 Key）",
        "settings.ollama_hint": "本地模型：需先安装 Ollama 并运行（ollama pull qwen2.5vl:7b），无需 API Key，完全离线免费。",
        "settings.no_key_hint": "该服务无需 API Key。",
        "settings.need_key_hint": "该服务需要 API Key，请在对应平台获取后填入上方。",
        # 语言选项
        "lang.auto": "自动识别",
        "lang.zh": "中文",
        "lang.en": "英文",
        "lang.ja": "日文",
        "lang.ko": "韩文",
        # 界面语言
        "settings.ui_lang": "界面语言：",
        "ui_lang.zh": "中文",
        "ui_lang.en": "English",
        # 悬浮窗位置
        "settings.overlay_position": "译文悬浮窗位置：",
        "pos.top_left": "左上角",
        "pos.top_right": "右上角",
        "pos.bottom_left": "左下角",
        "pos.bottom_right": "右下角",
        # 快捷键动作
        "hotkey.capture_translate": "截图并翻译",
        "hotkey.retranslate": "重新翻译",
        "hotkey.copy_last": "复制译文",
        "hotkey.toggle_window": "显示/隐藏主窗口",
        "hotkey.select_region": "选择聊天区域",
        "hotkey.reply_translate": "翻译并复制（反向翻译）",
        "hotkey.cancel": "取消/关闭",
    },
    "en": {
        "app.title": "LoL Chat Translator",
        "app.brand": "LoL Translate",
        "nav.translate": "🖥  Translate",
        "nav.settings": "⚙  Settings",
        "status.ready": "Ready · Press F6 to capture",
        "btn.capture": "📷 Capture",
        "btn.select_region": "Select Region",
        "label.output_lang": "Output",
        "label.naturalness": "Naturalness",
        "label.literal": "Literal",
        "label.colloquial": "Colloquial",
        "label.result": "Translation",
        "label.reply": "Reply (type Chinese, translate to target)",
        "placeholder.result": "Translation appears here…\n\nPress F6 to capture, or type below to reply.",
        "placeholder.reply": "e.g. Come gank mid, thanks",
        "btn.reply": "Translate & Copy",
        "hint.reply_empty": "Please type something first",
        "hint.reply_ing": "Translating…",
        "hint.reply_done": "Translated & copied to clipboard",
        "settings.title": "Settings",
        "settings.tab.provider": "Provider",
        "settings.tab.language": "Language",
        "settings.tab.hotkey": "Hotkeys",
        "settings.provider": "Provider:",
        "settings.api_key": "API Key:",
        "settings.base_url": "Base URL:",
        "settings.model": "Model:",
        "settings.model_hint": "Model must support vision/image input",
        "settings.test": "Test Connection",
        "settings.source_lang": "Source language:",
        "settings.target_lang": "Screenshot target language:",
        "settings.lang_hint": "Source defaults to auto-detect.",
        "settings.reset_hotkey": "Reset Default Hotkeys",
        "settings.hotkey_hint": "Keys: f1-f12, home, end, insert, delete, page up/down, ctrl+alt+letter",
        "settings.clear_key": "Clear Key",
        "settings.save": "Save",
        "settings.warn_key_required": "API Key is required (not needed for local Ollama)",
        "settings.ollama_hint": "Local model: install Ollama first (ollama pull qwen2.5vl:7b). No API key, fully offline & free.",
        "settings.no_key_hint": "This provider does not require an API key.",
        "settings.need_key_hint": "This provider requires an API key.",
        "lang.auto": "Auto Detect",
        "lang.zh": "Chinese",
        "lang.en": "English",
        "lang.ja": "Japanese",
        "lang.ko": "Korean",
        "settings.ui_lang": "UI Language:",
        "ui_lang.zh": "中文",
        "ui_lang.en": "English",
        # 悬浮窗位置
        "settings.overlay_position": "Overlay position:",
        "pos.top_left": "Top-left",
        "pos.top_right": "Top-right",
        "pos.bottom_left": "Bottom-left",
        "pos.bottom_right": "Bottom-right",
        "hotkey.capture_translate": "Capture & Translate",
        "hotkey.retranslate": "Re-translate",
        "hotkey.copy_last": "Copy Translation",
        "hotkey.toggle_window": "Show/Hide Window",
        "hotkey.select_region": "Select Chat Region",
        "hotkey.reply_translate": "Translate & Copy (Reply)",
        "hotkey.cancel": "Cancel/Close",
    },
}


def set_language(lang: str):
    global _current_lang
    if lang in MESSAGES:
        _current_lang = lang


def get_language() -> str:
    return _current_lang


def tr(key: str) -> str:
    """取当前语言的文案，找不到时回退中文，再回退 key 本身。"""
    return (
        MESSAGES.get(_current_lang, {}).get(key)
        or MESSAGES["zh"].get(key)
        or key
    )

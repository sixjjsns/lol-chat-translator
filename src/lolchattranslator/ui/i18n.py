"""国际化（i18n）：界面语言中英切换。

使用简单的字典 + 全局当前语言，避免引入重型框架。
UI 层通过 tr(key) 取文案，切换语言后调用各页面的 apply_language() 刷新。
"""

# 当前界面语言：zh / en
_current_lang = "zh"

MESSAGES = {
    "zh": {
        "app.title": "LOL国际服聊天框翻译",
        "app.brand": "LoL 翻译",
        "nav.section": "工作区",
        "nav.translate": "翻译",
        "nav.settings": "设置",
        "status.ready": "就绪 · F6 截取聊天区域，F10 翻译并注入",

        # 顶栏
        "page.translate.title": "翻译",
        "page.translate.subtitle": "看懂队友在说什么，再用对方的语言回过去",
        "page.settings.title": "设置",
        "page.settings.subtitle": "翻译服务、语言、注入与快捷键",

        # 翻译页
        "btn.capture": "截取聊天",
        "btn.select_region": "选区域",
        "btn.retranslate": "重译",
        "btn.copy": "复制",
        "btn.reply_inject": "翻译并注入",
        "btn.reply_copy": "翻译并复制",
        "label.output_lang": "输出",
        "label.naturalness_short": "语气",
        "label.quick_phrases": "快捷短语（点一下直接翻译并注入）",
        "label.preview_empty": "将发送：—",
        "label.preview_done": "将发送：{text}",
        "placeholder.result": "译文会出现在这里。\n\n按 F6 截取聊天区域，或直接在下方输入中文回复。",
        "placeholder.reply": "例如：来中路抓一下，谢谢",
        "hint.reply_empty": "请先输入要翻译的内容",
        "hint.reply_empty_out": "未识别到内容，请重试",
        "hint.reply_ing": "翻译中…",
        "card.result_title": "队友在说什么",
        "card.result_hint": "最近 5 条",
        "card.reply_title": "我要回什么",
        "card.reply_hint": "输入中文",
        "chip.region_set": "区域已设置",
        "chip.region_unset": "区域未设置",
        "chip.inject_on": "自动注入 · 开",
        "chip.inject_off": "自动注入 · 关",
        "tip.capture": "截取预设的聊天区域并翻译（F6）",
        "tip.inject_state": "开启后，F10 会把译文直接打进游戏聊天框",

        # 设置页
        "settings.title": "设置",
        "settings.tab.provider": "翻译服务",
        "settings.tab.language": "语言与界面",
        "settings.tab.paste": "注入",
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
        "settings.auto_paste": "把译文自动注入游戏聊天框（有封号风险，谨慎开启）",
        "settings.auto_paste_warn": "警告：自动注入通过 SendInput 向游戏窗口发送按键，可能违反游戏服务条款。开启后 F10 会直接把译文打进聊天框，但不会自动发送，仍需你按 Enter。",
        "settings.paste_delay": "注入延迟（每个字符）：",

        # 语言
        "lang.auto": "自动识别",
        "lang.zh": "中文",
        "lang.en": "英文",
        "lang.ja": "日文",
        "lang.ko": "韩文",
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
        "hotkey.reply_translate": "翻译并注入",
        "hotkey.cancel": "取消/关闭",
    },
    "en": {
        "app.title": "LoL International Server Chat Translator",
        "app.brand": "LoL Translate",
        "nav.section": "WORKSPACE",
        "nav.translate": "Translate",
        "nav.settings": "Settings",
        "status.ready": "Ready · F6 to capture, F10 to translate & inject",

        "page.translate.title": "Translate",
        "page.translate.subtitle": "Understand your team, answer in their language",
        "page.settings.title": "Settings",
        "page.settings.subtitle": "Provider, language, injection and hotkeys",

        "btn.capture": "Capture",
        "btn.select_region": "Region",
        "btn.retranslate": "Retry",
        "btn.copy": "Copy",
        "btn.reply_inject": "Translate & Inject",
        "btn.reply_copy": "Translate & Copy",
        "label.output_lang": "Output",
        "label.naturalness_short": "Tone",
        "label.quick_phrases": "Quick phrases (click to translate & inject)",
        "label.preview_empty": "Sending: —",
        "label.preview_done": "Sending: {text}",
        "placeholder.result": "Translations appear here.\n\nPress F6 to capture chat, or type a reply below.",
        "placeholder.reply": "e.g. Come gank mid, thanks",
        "hint.reply_empty": "Please type something first",
        "hint.reply_empty_out": "Nothing recognised, please retry",
        "hint.reply_ing": "Translating…",
        "card.result_title": "What teammates say",
        "card.result_hint": "last 5",
        "card.reply_title": "What I want to say",
        "card.reply_hint": "type in Chinese",
        "chip.region_set": "Region set",
        "chip.region_unset": "No region",
        "chip.inject_on": "Auto-inject · ON",
        "chip.inject_off": "Auto-inject · OFF",
        "tip.capture": "Capture the preset chat region and translate (F6)",
        "tip.inject_state": "When on, F10 types the translation straight into game chat",

        "settings.title": "Settings",
        "settings.tab.provider": "Provider",
        "settings.tab.language": "Language & UI",
        "settings.tab.paste": "Injection",
        "settings.tab.hotkey": "Hotkeys",
        "settings.provider": "Provider:",
        "settings.api_key": "API Key:",
        "settings.base_url": "Base URL:",
        "settings.model": "Model:",
        "settings.model_hint": "Model must support vision / image input",
        "settings.test": "Test Connection",
        "settings.source_lang": "Source language:",
        "settings.target_lang": "Screenshot target language:",
        "settings.lang_hint": "Source defaults to auto-detect.",
        "settings.reset_hotkey": "Reset Default Hotkeys",
        "settings.hotkey_hint": "Keys: f1-f12, home, end, insert, delete, page up/down, ctrl+alt+letter",
        "settings.clear_key": "Clear Key",
        "settings.save": "Save",
        "settings.warn_key_required": "API Key is required (not needed for local Ollama)",
        "settings.ollama_hint": "Local model: install Ollama first (ollama pull qwen2.5vl:7b). No API key, fully offline.",
        "settings.no_key_hint": "This provider does not require an API key.",
        "settings.need_key_hint": "This provider requires an API key.",
        "settings.auto_paste": "Auto-inject translation into game chat (ban risk, use with caution)",
        "settings.auto_paste_warn": "Warning: auto-inject sends keystrokes to the game window via SendInput and may violate the game's Terms of Service. It never sends the message — you still press Enter.",
        "settings.paste_delay": "Injection delay (per char):",

        "lang.auto": "Auto Detect",
        "lang.zh": "Chinese",
        "lang.en": "English",
        "lang.ja": "Japanese",
        "lang.ko": "Korean",
        "settings.ui_lang": "UI Language:",
        "ui_lang.zh": "中文",
        "ui_lang.en": "English",

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
        "hotkey.reply_translate": "Translate & Inject",
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

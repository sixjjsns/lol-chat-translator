# Changelog / 更新日志

All notable changes to this project will be documented in this file.
本项目的所有重要变更都会记录在此文件中。

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).
格式遵循 [Keep a Changelog](https://keepachangelog.com/)，版本号遵循 [语义化版本](https://semver.org/)。

## [Unreleased] / 未发布

## [1.2.0] - 2026-10-30

### Added / 新增

- **快捷短语 (Quick phrases)**:翻译页内置 6 句 LoL 高频用语(来中路抓一下 / 打野在下路 / 我去做视野 / 别送稳住 / 抱团推塔 / 打得不错),点一下直接翻译并注入,不用打字。
- **Toast 轻提示**:替代旧版游戏内回复悬浮窗,2.6 秒自动淡出、鼠标穿透、不抢焦点,只在屏幕底部中间显示「已注入 / 已复制 / 失败原因」。
- **译文历史带时间戳**:译文区改用 HTML 渲染,每条带 `HH:MM:SS` 时间戳与分隔线,连续 F6 时上下文更清晰。
- **状态胶囊**:顶栏实时显示当前服务(如「智谱 GLM-4V」)与自动注入开关;翻译页顶部显示截图区域是否已设置。
- **侧边栏快捷键卡**:实时显示当前生效的 F6 / F10 / F7 / F8,改键后立刻更新。

### Changed / 变更

- **界面整体重做**:卡片式双区布局(队友在说什么 / 我要回什么)、品牌侧边栏 + 顶栏、金色渐变主按钮、圆角状态胶囊、深色标题栏(DWM);设置页按钮层级重做(主按钮金色 / 清除红色 / 测试连接定宽)。
- **反向翻译结果不再覆盖输入框**:翻译结果进入「将发送」预览行,输入框保留原文,改完可以再次翻译。
- **F10 链路简化**:翻译 → 直接注入游戏聊天框(核心 SendInput 注入逻辑未改动)→ Toast 反馈;未开启自动注入或注入失败时自动复制到剪贴板兜底。

### Removed / 移除

- **游戏内 F10 回复草稿悬浮窗**(`ui/reply_overlay.py`):挡画面、需要手动关闭,已由 Toast 取代。F6 的只读阅读悬浮窗保留。

### Fixed / 修复

- 语言切换后标题、按钮、快捷键卡文案不刷新的问题。
- 版本号统一为 1.2.0(`pyproject.toml` / 侧边栏 / README)。


## [1.1.0] - 2026-10-28

### Added / 新增

- **智谱 GLM-4V 视觉模型支持**:新增 zhipu provider,base_url `https://open.bigmodel.cn/api/paas/v4`,默认模型 `glm-4v-plus`,解决 DeepSeek 视觉模型对游戏聊天框小字识别率过低的问题。GLM-4V 识图能力强,新用户 2000 万免费 token + 120 次图像资源包,日常使用几乎不花钱(单张截图约 ¥0.008)。
- **自动补全(自动粘贴)注入功能**:F10 反向翻译完成后,程序主动抢焦点并尝试向游戏聊天框注入译文(SendInput + KEYEVENTF_UNICODE)。配置开关 `paste.auto_paste`,默认关闭(高风险,需用户显式开启)。
- **回复草稿悬浮窗(F10)**:绿色边框,可编辑,带「复制」按钮,作为自动注入失败时的兜底回填路径。
- **译文历史保留最近 5 条**:连续 F6 截图多次,译文区按时间顺序累积展示,分隔线区分,自动滚到最新一条,避免"看不过来"。
- **截图小区域自动放大 2 倍**:聊天框局部截图(短边 <400px)用 LANCZOS 放大,提升小字 OCR 识别率。

### Changed / 变更

- **悬浮窗 UX 优化**:阅读悬浮窗(金色,只读,F6 截图翻译结果)和回复草稿悬浮窗(绿色,可编辑,F10 反向翻译结果)严格区分,避免混淆;两者均支持拖动、右键菜单、Esc 关闭。
- **焦点注入逻辑修复**:`_focus_game_window` 改回主动抢焦点(SetForegroundWindow + AttachThreadInput + BringWindowToTop),不再"前台不是游戏就放弃"导致一次都没注入。
- **翻译 Prompt 大幅升级(双向真人化)**:接收端和发送端的 system prompt 都加入英雄联盟完整术语词典(位置/技能/资源/战术/俚语/各国笑法),提供大量错误 vs 正确对照例子,强调"能缩写就缩写、该用俚语就用俚语",避免中式外语机翻。
- **视觉模型 content 健壮性**:处理 content 为 None/空/列表(多模态)的情况,空内容明确提示"未识别到聊天内容"。

### Fixed / 修复

- **SendInput 结构体 32 字节错误**:`_InputUnion` 缺失分支导致 sizeof(INPUT) 偏小被拒,补全 mi/ki/hi 三分支(应为 40B)。
- **截图翻译语言冲突**:截图翻译与界面下拉框共用语言源,统一改用 `config.language.target`。
- **快捷键 home 键冲突**:删除已废弃的 `toggle_overlay` 动作,加配置迁移自动清理旧值。
- **配置迁移**:自动升级 `image_detail: low → high`、`max_tokens: 2048 → 512`,清理历史残留字段。

## [1.0.0] - 2026-10-27

### Added / 新增

- PySide6-based modern UI with sidebar navigation. 基于 PySide6 的现代化界面,带侧边导航。
- Screenshot translation (capture chat region → vision LLM → translated text). 截图翻译(截取聊天区域 → 视觉大模型 → 译文)。
- Reverse translation (type Chinese → translate to opponent's language). 反向翻译(输入中文 → 翻译成对方语言)。
- Multi-provider support: DeepSeek, OpenAI GPT, Google Gemini, xAI Grok, Moonshot Kimi, local Ollama. 多服务支持:DeepSeek、OpenAI GPT、Google Gemini、xAI Grok、Moonshot Kimi、本地 Ollama。
- Naturalness slider (maps to model temperature). 人性化滑块(映射为模型 temperature)。
- Global hotkeys with debounce and conflict detection. 全局快捷键,带防抖与冲突检测。
- System tray integration. 系统托盘集成。
- SQLite-ready layered architecture (core/providers/services/infrastructure). 面向 SQLite 的分层架构(core/providers/services/infrastructure)。

## [0.1.0] - Initial / 初始版本

- Core translation pipeline and OpenAI-compatible provider layer. 核心翻译流水线与 OpenAI 兼容的 Provider 层。

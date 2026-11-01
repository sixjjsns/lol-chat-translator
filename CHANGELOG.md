# Changelog / 更新日志

All notable changes to this project will be documented in this file.
本项目的所有重要变更都会记录在此文件中。

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).
格式遵循 [Keep a Changelog](https://keepachangelog.com/)，版本号遵循 [语义化版本](https://semver.org/)。

## [Unreleased] / 未发布

## [1.2.2] - 2026-11-01

### Fixed / 修复

- **模型偶尔"回答"而不是翻译（本次核心）**：输入「能不能说中文」时，模型回「当然可以，我可以用中文与您交流…」（已用真实模型复现）。
  根因是旧 Prompt 只强调"像真人"，**没有输出契约**，也没把"待翻译文本"和"对你说的指令"区分开。
  现在三层防御：角色固定为翻译引擎 + 输入用 `<<< >>>` 包裹并声明"问句/命令也只翻译不回答" + 输出清理与检测，
  命中"在回答问题"时自动用**严格模式**（超短 Prompt、0.2 温度）重试一次（`api.strict_translate`，默认开）。
- **截图翻译缓存串味**：缓存键只哈希了图片，改「目标语言」或「语气」后 60 秒内仍返回旧译文。现在键包含目标语言与温度。
- **翻译温度过高**：人性化滑块拉满时温度 1.0，容易发散和胡编；翻译场景温度上限裁到 0.6。

### Changed / 变更

- **术语库重写**：按 位置 / 技能 / 资源 / 打野 / 宏观 / 信息 / 俚语 / 语气 分类，补充 tp、plates、soul、proxy、freeze、slow push、dive、kite、peel 等 60+ 条；
  新增中英日韩四种语言的**整句对照**（ss / omw / oom / jg diff / 666 / 你怎么这么菜 等），并按语体给示例（日语常体、韩语반말省略代词）。
- 反向翻译输出 token 上限 300，从物理上限制"巴拉巴拉一大堆"。
- 版本号统一为 1.2.2。


## [1.2.1] - 2026-11-01

### Added / 新增

- **译文悬浮窗 F11 隐藏/呼出**:新增全局快捷键 `toggle_overlay`(默认 F11)。游戏内一键收起译文窗口,再按一次呼出最近一条译文;侧边栏快捷键卡同步显示。
- **译文悬浮窗自动隐藏**:默认 15 秒后自动隐藏,鼠标悬停暂停计时、移开重新计时;设置页可调时长(0 = 常驻)。
- **鼠标穿透模式**:悬浮窗右键菜单可开启,开启后所有点击直接穿过窗口落到游戏里,配合 F11 关闭,完全不挡操作。

### Fixed / 修复

- **悬浮窗拖不动**:旧版正文 QLabel 开启了文字选择,把鼠标按下事件全部吃掉,只有标题栏和边距几像素能拖。现在按住窗口**任意位置**都能拖动,复制译文移到右键菜单。
- **译文跑出屏幕**:旧版先定位再 `adjustSize()`,窗口变大后下半截伸到屏幕外。现在先定尺寸(限制最大为屏幕的 55%×45%)再定位,并把窗口钳制在屏幕可用区域内,四个角都不会越界。
- 设置页新增「译文悬浮窗自动隐藏」时长选项;快捷键列表新增 F11 项;快捷键配置迁移不再删除 `toggle_overlay`。

### Changed / 变更

- `ui/result_overlay.py` 重写:标题栏新增拖动手柄与关闭按钮,支持任意位置拖动、右键菜单(复制译文/鼠标穿透/关闭)。
- 版本号统一为 1.2.1。


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

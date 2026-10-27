# Changelog / 更新日志

All notable changes to this project will be documented in this file.
本项目的所有重要变更都会记录在此文件中。

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).
格式遵循 [Keep a Changelog](https://keepachangelog.com/)，版本号遵循 [语义化版本](https://semver.org/)。

## [Unreleased] / 未发布

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

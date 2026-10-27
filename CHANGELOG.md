# Changelog / 更新日志

All notable changes to this project will be documented in this file.
本项目的所有重要变更都会记录在此文件中。

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).
格式遵循 [Keep a Changelog](https://keepachangelog.com/)，版本号遵循 [语义化版本](https://semver.org/)。

## [Unreleased] / 未发布

### Added / 新增

- PySide6-based modern UI with sidebar navigation. 基于 PySide6 的现代化界面，带侧边导航。
- Screenshot translation (capture chat region → vision LLM → translated text). 截图翻译（截取聊天区域 → 视觉大模型 → 译文）。
- Reverse translation (type Chinese → translate to opponent's language). 反向翻译（输入中文 → 翻译成对方语言）。
- Multi-provider support: DeepSeek, OpenAI GPT, Google Gemini, xAI Grok, Moonshot Kimi, local Ollama. 多服务支持：DeepSeek、OpenAI GPT、Google Gemini、xAI Grok、Moonshot Kimi、本地 Ollama。
- Naturalness slider (maps to model temperature). 人性化滑块（映射为模型 temperature）。
- Global hotkeys with debounce and conflict detection. 全局快捷键，带防抖与冲突检测。
- System tray integration. 系统托盘集成。
- SQLite-ready layered architecture (core/providers/services/infrastructure). 面向 SQLite 的分层架构（core/providers/services/infrastructure）。

## [0.1.0] - Initial / 初始版本

- Core translation pipeline and OpenAI-compatible provider layer. 核心翻译流水线与 OpenAI 兼容的 Provider 层。

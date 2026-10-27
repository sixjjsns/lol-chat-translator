# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- PySide6-based modern UI with sidebar navigation.
- Screenshot translation (capture chat region → vision LLM → translated text).
- Reverse translation (type Chinese → translate to opponent's language).
- Multi-provider support: DeepSeek, OpenAI GPT, Google Gemini, Groq, Moonshot Kimi, local Ollama.
- Naturalness slider (maps to model temperature).
- Global hotkeys with debounce and conflict detection.
- System tray integration.
- SQLite-ready layered architecture (core/providers/services/infrastructure).

## [0.1.0] - Initial

- Core translation pipeline and OpenAI-compatible provider layer.

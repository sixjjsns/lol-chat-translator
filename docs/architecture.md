# Architecture / 架构说明

## Overview / 总览

LoL Chat Translator 采用分层架构，将 UI（PySide6）、业务核心（翻译服务）、
Provider（多服务适配）与基础设施（配置/密钥/日志）解耦。

```
┌─────────────────────────────────────────────┐
│                    UI 层                     │
│  main_window / pages / theme / region_selector│
└──────────────────┬──────────────────────────┘
                   │ Qt 信号槽
┌──────────────────▼──────────────────────────┐
│                  App 层                       │
│  application (编排) / task_manager (QThread)  │
│  lifecycle (单实例) / bootstrap (启动)         │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│                 Core 层                       │
│  models (数据模型) / translation_service (编排)│
└──────┬───────────────────────────┬──────────┘
       │                           │
┌──────▼──────────┐     ┌──────────▼──────────┐
│   Providers 层   │     │   Services 层        │
│ base/openai_compat│     │ screenshot/hotkey   │
│ registry/capabilities│  │ image_processor/tray│
└──────┬──────────┘     └─────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│            Infrastructure 层                 │
│  config_store / secret_store / logging_config│
└─────────────────────────────────────────────┘
```

## Threading model / 线程模型

- **主线程**：QApplication + MainWindow，所有 Qt 操作在主线程。
- **keyboard 线程**：全局快捷键回调（keyboard 库），通过 Qt 信号安全回传。
- **pystray 线程**：托盘菜单回调，同样通过信号回传。
- **TaskManager (QThread)**：翻译任务在 worker 线程执行，结果通过信号回传，
  避免阻塞 UI。

## Key design decisions / 关键设计决策

1. **单 Provider 协议**：所有云服务 + 本地 Ollama 统一走 OpenAI 兼容
   Chat Completions 格式，通过 `base_url` + `model` 区分。
2. **数据模型解耦**：`TranslationRequest` / `TranslationResult` 作为统一
   输入输出，UI 与核心逻辑只依赖模型，不依赖具体 Provider。
3. **缓存去重**：截图内容 SHA256 哈希，TTL 内相同截图不重复请求。
4. **人性化滑块**：0~100 映射到 temperature 0~1.0，动态调节口语化程度。

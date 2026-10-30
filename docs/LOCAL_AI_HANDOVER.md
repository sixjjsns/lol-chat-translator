# 本地 AI 接手交接文档 · LoL 国际服聊天框翻译

> 本文档面向接手本项目的本地 AI。读完本文档即可上手修改代码、提交、打包、发布,无需再向用户询问任何信息。

---

## TL;DR

- **项目**:LoL 国际服聊天框翻译(Windows 后台工具,Python + PySide6),解决跨服聊天沟通(看懂队友 + 用对方语言回复)。
- **GitHub 授权**:`gh` CLI 已在 Windows keyring 登录账号 `sixjjsns`,**无需明文 token**,本地 AI 直接调用 `gh`/`git` 命令即可。
- **本地目录**:`C:/Users/Administrator/Desktop/github/lol-chat-translator`
- **当前版本**:`v1.1.0`(已发布 Release)
- **核心改动重点(v1.1.0)**:接入智谱 GLM-4V(替代 DeepSeek 识图)、双悬浮窗严格分离、自动注入游戏聊天框、翻译 Prompt 双向真人化。

---

## 1. GitHub 授权方式(免登录)

**关键事实**:`gh` CLI 已经在系统钥匙串(keyring)登录账号 `sixjjsns`,token scopes 包含 `repo`、`workflow`、`admin:repo_hook`、`delete_repo`、`gist` 等完整权限。

**本地 AI 使用方式**:
- **不需要**手动配置任何 token、不需要写入 `~/.gitconfig` 的 credential helper、不需要环境变量
- 直接调用以下命令即可,系统会自动从 keyring 取凭据:
  ```bash
  gh auth status              # 验证登录状态
  git push origin master      # 推送代码
  gh release create vX.Y.Z ... # 创建 Release
  ```
- Git operations protocol: `https`

**禁止行为**:
- 不要把明文 token 写入任何文档、配置文件、commit message
- 不要执行 `gh auth logout` 或 `gh auth token` 输出明文 token

---

## 2. 仓库与目录信息

| 项目 | 值 |
|---|---|
| 远程仓库 | `https://github.com/sixjjsns/lol-chat-translator.git` |
| 本地工作目录 | `C:/Users/Administrator/Desktop/github/lol-chat-translator` |
| 主分支 | `master` |
| 最新 commit | `ae31a36 v1.1.0: 接入智谱 GLM-4V + 双悬浮窗 + 自动注入 + 翻译真人化` |
| 最新 tag | `v1.1.0` |
| git user.name(本仓库局部) | `sixjjsns` |
| git user.email(本仓库局部) | `sixjjsns@users.noreply.github.com` |

---

## 3. 项目概述

**项目名**:LOL国际服聊天框翻译(英文:LoL International Server Chat Translator)

**核心痛点**:LoL 国际服(日服/韩服/欧美服)队友含日本人、韩国人、欧美人,聊天跨语言。LoL 游戏内屏蔽了外部 Ctrl+V 程序化粘贴,普通翻译工具无法形成"看懂 + 回复"闭环。

**解决路径**:
1. F6 截图聊天框 → 视觉模型识别翻译 → 阅读悬浮窗显示
2. F10 输入中文 → 反向翻译 → 自动注入游戏聊天框(或悬浮窗兜底复制)

**技术栈**:
- Python 3.x + PySide6(Qt6 GUI)
- OpenAI 兼容 Chat Completions 协议(统一适配 DeepSeek/GPT/Gemini/Grok/Kimi/智谱 GLM-4V/Ollama)
- 视觉模型用 `image_url` + Base64
- mss 截图 + PIL 处理(局部区域 LANCZOS 自动放大 2 倍)
- keyboard 库全局快捷键 + pystray 托盘
- ctypes 实现 SendInput(KEYEVENTF_UNICODE)游戏窗口文本注入
- PyInstaller 打包(onefile spec)
- 虚拟环境:`.venv/`(项目根目录下)

---

## 4. 项目结构总览

```
lol-chat-translator/
├── main.py                                    # 入口
├── pyproject.toml                             # 依赖与元信息
├── LoLChatTranslator-onefile.spec             # PyInstaller 单文件 spec
├── LoLChatTranslator.spec                     # PyInstaller 目录版 spec
├── build.ps1                                  # 一键打包脚本
├── CHANGELOG.md                               # 更新日志(v1.0.0 / v1.1.0)
├── README.md                                  # 双语 README
├── config/
│   └── default_config.json                    # 默认配置(provider 列表/快捷键/paste 设置)
├── src/lolchattranslator/
│   ├── app/
│   │   ├── application.py                     # 应用主控制器(信号槽编排 UI/翻译/快捷键/托盘/任务)
│   │   └── task_manager.py                    # QThread worker,翻译任务异步执行
│   ├── core/
│   │   ├── models.py                          # TranslationRequest/TranslationResult/TaskKind
│   │   └── translation_service.py             # 翻译服务封装(调度 provider)
│   ├── infrastructure/
│   │   ├── config_store.py                    # 配置读写 + _migrate() 自动升级旧值
│   │   ├── secret_store.py                    # API Key 存储(本地文件 + XOR 弱混淆,wincred 兜底)
│   │   └── logging_config.py                  # 日志配置
│   ├── providers/
│   │   ├── base.py                            # BaseProvider/ProviderError
│   │   ├── openai_compat.py                   # 通用 OpenAI 兼容 Provider(含视觉翻译 + 双向 Prompt)
│   │   └── registry.py                        # PROVIDERS 注册表
│   ├── services/
│   │   ├── screenshot_service.py              # mss 截图 + 局部小区域自动 LANCZOS 放大 2 倍
│   │   ├── input_injector.py                  # SendInput KEYEVENTF_UNICODE 游戏聊天框注入(高风险)
│   │   ├── hotkey_service.py                  # 全局快捷键管理
│   │   └── tray_service.py                    # 系统托盘
│   ├── ui/
│   │   ├── main_window.py                     # 主窗口(侧边导航 + 翻译页/设置页)
│   │   ├── result_overlay.py                  # 阅读悬浮窗(金色,只读,F6 截图翻译结果)
│   │   ├── reply_overlay.py                   # 回复草稿悬浮窗(绿色,可编辑,F10 反向翻译结果)
│   │   ├── region_selector.py                 # F9 截图区域选择器
│   │   ├── i18n.py                            # 中英双语文案
│   │   ├── components/                        # 通用组件
│   │   ├── dialogs/                           # 对话框
│   │   └── pages/
│   │       ├── translation_page.py            # 翻译页(译文历史保留最近 5 条)
│   │       └── settings_page.py               # 设置页(provider/key/语言/快捷键/自动粘贴)
│   └── resources/
│       ├── icons/                             # 多尺寸 app_icon.ico
│       └── styles/                            # QSS 样式
└── tests/unit/                                # 单元测试
```

---

## 5. 核心架构分层说明

项目采用**面向 SQLite 的分层架构**(虽然当前未用 SQLite,但目录结构预留):

| 层 | 目录 | 职责 |
|---|---|---|
| **app** | `app/` | 应用主控制器,用 Qt 信号槽编排 UI、翻译服务、快捷键、托盘、任务管理器之间的协作 |
| **core** | `core/` | 领域模型(TranslationRequest/Result/TaskKind)+ 翻译服务封装 |
| **providers** | `providers/` | LLM Provider 抽象层,统一 OpenAI 兼容协议 |
| **services** | `services/` | 截图、输入注入、快捷键、托盘等系统服务 |
| **ui** | `ui/` | PySide6 界面组件 |
| **infrastructure** | `infrastructure/` | 配置存储、密钥存储、日志 |

**信号槽协作机制**(关键):
- 主线程:QApplication + MainWindow,所有 Qt 操作都在主线程
- keyboard 线程:全局快捷键回调,通过 `_Bridge(QObject)` 的 `actionTriggered` 信号安全投递到主线程
- pystray 线程:托盘菜单回调,同样通过 bridge 信号回传主线程
- TaskManager(QThread):翻译任务在 worker 线程执行,结果通过 `finished`/`failed` 信号回传

**禁忌**:绝对不要在 keyboard/pystray/TaskManager 线程里直接操作 Qt 控件,会死锁/白屏。必须通过信号槽跨线程投递。

---

## 6. 关键模块实现思路(v1.1.0 重点)

### 6.1 智谱 GLM-4V 接入(识图识别率问题的解)

**问题根因**:DeepSeek-flash 视觉模型对 LoL 聊天框小字 OCR 识别率极低(实测成功率 <30%,大量返回空 content),导致"截图整个屏幕都识别不到"。日志中大量 `视觉翻译返回空内容` 警告。

**解法**:新增 zhipu provider。
- base_url:`https://open.bigmodel.cn/api/paas/v4`(注意**没有 `/v1`**,与 DeepSeek 不同)
- model:`glm-4v-plus`(识图模型,价格 ¥4/百万 token,新用户送 2000 万 token + 120 次图像资源包,单张图约 ¥0.008)
- GLM-4V 识图能力强,识别率显著高于 DeepSeek

**代码改动点**:
- `providers/registry.py`:`PROVIDERS` 字典加 `"zhipu": OpenAICompatProvider`
- `config/default_config.json`:`providers.zhipu` 配置块
- 用户实例 `config.json` 中 `api.provider` 切到 `"zhipu"`
- `OpenAICompatProvider` 是通用类,智谱官方提供 OpenAI 兼容端点,只需切 base_url + model 即可适配,无需新写 Provider 类

### 6.2 双悬浮窗架构(避免混淆)

**设计原则**:F6 截图翻译(看队友消息,只读)和 F10 反向翻译(发队友消息,可编辑)**语义完全相反**,绝不能用同一个悬浮窗。这是项目演进中踩过的坑——曾经合并导致"翻译和回复混淆"。

**实现**:
- `result_overlay.py` → `ResultOverlayWindow`
  - 金色边框 `#c9a24b`
  - `QLabel` 只读(可鼠标选中文字)
  - 显示 F6 截图翻译结果
- `reply_overlay.py` → `ReplyOverlayWindow`
  - 绿色边框 `#4caf7d`
  - `QTextEdit` 可编辑
  - 带「复制」按钮(点击写入剪贴板,800ms 后按钮文字恢复)
  - 显示 F10 反向翻译结果
- 两者共同特性:无边框、置顶、半透明、可拖动(按住窗口空白区域)、右键菜单、Esc 关闭
- `application.py` 的 `_on_task_finished` 按 `result.kind` 分流:
  - `TaskKind.REPLY` → reply_overlay
  - 其他(截图翻译)→ result_overlay

### 6.3 自动注入(SendInput KEYEVENTF_UNICODE)

**目的**:F10 翻译完成后,把译文自动注入到游戏聊天框。LoL 屏蔽了 Ctrl+V 程序化粘贴,只能模拟键盘按键。

**实现**(`services/input_injector.py`):
- 用 ctypes 定义 `INPUT` 结构体(x64 下必须为 40 字节)
  - `_InputUnion` 必须含 mi/ki/hi 三分支,**缺失分支会导致 sizeof(INPUT) 偏小被 SendInput 拒绝**(曾经踩过 32 字节的坑)
- `KEYEVENTF_UNICODE` 逐 UTF-16 码元注入(支持 BMP 字符 + 增补平面字符如 emoji,后者拆成高/低代理对)
- 带 ±50% 随机延迟抖动模拟真人打字节奏,降低反作弊启发式命中概率

**焦点逻辑**(关键,别改坏):
- `_focus_game_window()` 必须**主动抢焦点**:`SetForegroundWindow` + `AttachThreadInput` + `BringWindowToTop`,最小化先 `SW_RESTORE`
- **绝对不要**改成"前台非游戏就 return 0 放弃"——曾经改过这个,导致 F10 触发时焦点必在本工具上,每次都 return 0,**一次都没真正注入**,用户测"日语打不进"其实是根本没注入
- 抢焦点后 `time.sleep(0.15)` 给系统时间完成前台切换

**双路兜底**(`application.py` 的 REPLY 分支):
1. 主路径:自动注入(需 `paste.auto_paste=true` 配置开启)
2. 兜底:**无论如何都弹回复草稿窗**,失败时用户可手动 Ctrl+V

**重要约束**:本模块不会自动按 Enter 发送,由用户确认后手动发送。注入仅填文本到聊天框。

### 6.4 翻译 Prompt 双向真人化

**位置**:`providers/openai_compat.py`
- `_system_prompt(target_lang)`:接收端(F6 截图翻译,把队友消息翻成中文)
- `_reply_system_prompt(target_lang)`:发送端(F10 反向翻译,把中文翻成对方语言)

**核心升级**:
- 加入 LoL 完整术语词典:
  - 位置:top/mid/jg/adc/bot/sup
  - 技能:ult/cc/smite/flash/q-w-e-r
  - 资源:baron/dragon/herald/buff/tower/inhib/nexus
  - 战术:gank/push/defend/split/roam/back/ward/group/engage/peel/kite/focus/ss/mia/re/omw/oom
  - 俚语:gg/wp/gj/mb/glhf/diff/noob/feeder/afk/ks/int/ez/report
  - 各国笑:zzzzz(韩)、wwwww(日)、lol(英)、ㅋㅋㅋ(韩)
- 提供大量错误 vs 正确对照例子:
  - 错误(中式英语):"you are very vegetable" → 正确:"you're so bad"
  - 错误(中式日语):"あなたはとても野菜です" → 正确:"お前杂鱼すぎ"
- 强调"能缩写就缩写、该用俚语就用俚语"
- **两端都做了同等升级**,不只是发送端

### 6.5 译文历史最近 5 条

`translation_page.py`:
- `__init__` 中 `self._history: list[str] = []`,`self._MAX_HISTORY = 5`
- `set_result(text)`:累积到 history,超过 5 条丢最旧,用分隔线 `──────` 拼接展示,新译文在底部,自动滚到底部
- `get_result()`:返回最新一条(不是整段历史),快捷键复制的是最新的
- `clear_result()`:同时清空 history 和 result_edit

### 6.6 截图小区域自动放大

`screenshot_service.py` 的 `_maybe_upscale(img)`:
- 短边 <400px 视为"局部截图"(聊天框通常很窄/很矮)
- 用 `PIL.Image.Resampling.LANCZOS` 放大 2 倍
- 全屏截图不放大,避免图片过大拖慢上传

### 6.7 配置迁移

`infrastructure/config_store.py` 的 `_migrate()`:
- 自动升级 `image_detail: low → high`
- 自动升级 `max_tokens: 2048 → 512`
- 清理 `toggle_overlay` 残留字段(已废弃的快捷键动作)

### 6.8 视觉模型 content 健壮性

`providers/openai_compat.py` 的 `vision_translate`:
- content 为 None → 空串
- content 为 list(多模态结构) → 拼接所有 text 片段
- 空内容 → 明确 warning 日志 + 用户提示"未识别到聊天内容"

---

## 7. 运行时配置位置(绝对路径)

| 用途 | 路径 |
|---|---|
| 用户实例配置 | `C:/Users/Administrator/AppData/Roaming/LoLChatTranslator/config.json` |
| API Key 存储 | `C:/Users/Administrator/AppData/Roaming/LoLChatTranslator/.credential`(XOR 弱混淆 JSON) |
| 运行日志 | `C:/Users/Administrator/AppData/Roaming/LoLChatTranslator/logs/app.log` |
| 默认配置模板 | `C:/Users/Administrator/Desktop/github/lol-chat-translator/config/default_config.json` |

**当前实例配置关键值**:
- `api.provider`: `zhipu`
- `api.base_url`: `https://open.bigmodel.cn/api/paas/v4`
- `api.model`: `glm-4v-plus`
- `paste.auto_paste`: `true`
- 快捷键:F6 截图翻译、F7 重译、F8 复制译文、F9 选区域、F10 反向翻译、Esc 取消

**API Key 存储说明**:
- 文件格式:`{"key": "<XOR 弱混淆字符串>"}`
- 账号名:`deepseek_api_key`(历史命名,但 provider 无关,所有 provider 共用此 key)
- 弱混淆算法:`chr(ord(c) ^ 0x5A)`,**不是安全加密**,仅防明文一眼泄露
- 不要把 key 写入源码、日志、配置 JSON

---

## 8. 打包流程

**前置清理(必须)**:打包前必须停掉正在运行的旧版 exe,否则 dist/ 被锁,`rm -rf dist` 会失败。

```bash
# 1. 停旧进程
tasklist | grep -i "LoLChat"
taskkill //F //IM LoLChatTranslator-onefile.exe

# 2. 清理旧产物
cd "C:/Users/Administrator/Desktop/github/lol-chat-translator"
rm -rf build dist

# 3. 打包(用 spec 文件)
.venv/Scripts/python.exe -m PyInstaller --noconfirm --clean LoLChatTranslator-onefile.spec
```

**产物**:`dist/LoLChatTranslator-onefile.exe`(约 61MB)

**Release 包重命名**(可选,用于上传 GitHub Release):
```bash
cp dist/LoLChatTranslator-onefile.exe dist/LoLChatTranslator-vX.Y.Z-win64.exe
```

---

## 9. GitHub 操作命令清单

### 9.1 提交代码
```bash
cd "C:/Users/Administrator/Desktop/github/lol-chat-translator"
git add -A
git commit -m "vX.Y.Z: 简要描述

主要变更:
- 变更点 1
- 变更点 2

详见 CHANGELOG.md"
```

### 9.2 打 tag 并推送
```bash
git tag vX.Y.Z
git push origin master
git push origin vX.Y.Z
```

### 9.3 创建 GitHub Release 并上传 exe
```bash
gh release create vX.Y.Z dist/LoLChatTranslator-vX.Y.Z-win64.exe \
  --title "vX.Y.Z: 标题" \
  --notes "## 主要变更
### 新增
- ...
### 修复
- ...

详见 CHANGELOG.md。

## 下载
- Windows 64 位安装包:LoLChatTranslator-vX.Y.Z-win64.exe(下方 Assets)"
```

### 9.4 其他常用命令
```bash
gh auth status                          # 验证登录
git log --oneline -5                    # 查看最近 5 个 commit
git remote -v                           # 查看远程
gh release list                         # 列出所有 Release
gh release view vX.Y.Z                  # 查看某个 Release 详情
```

### 9.5 CHANGELOG.md 更新规范
每次发版必须在 `CHANGELOG.md` 加入新版本段落,放在 `## [Unreleased]` 下方:
```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added / 新增
- ...

### Changed / 变更
- ...

### Fixed / 修复
- ...
```

---

## 10. 常见陷阱与已知问题(必读)

1. **DeepSeek 视觉模型识图能力弱,不要再用**:DeepSeek-flash 对 LoL 聊天框小字 OCR 成功率 <30%,大量返回空 content。项目已切到智谱 GLM-4V,**不要回切 DeepSeek 做识图**。

2. **SendInput 注入对 LoL 不一定有效,需用户手动 Ctrl+V 兜底**:即使抢焦点成功,`KEYEVENTF_UNICODE` 注入 LoL 也可能不认(LoL 只认 IME 组字后上屏的 `WM_CHAR`)。所以 `application.py` 的 REPLY 分支必须保留"无论如何都弹回复草稿窗"的兜底逻辑,**不要把悬浮窗兜底去掉**。

3. **焦点逻辑别改回"不抢焦点"**:`input_injector.py` 的 `_focus_game_window()` 必须**主动抢焦点**。曾经改成"前台非游戏就 return 0 放弃",导致 F10 触发时焦点必在本工具上,每次都 return 0,**一次都没真正注入**,用户测"打不进"其实是根本没注入。

4. **打包前必须 taskkill 旧进程**:否则 `dist/` 被锁,`rm -rf dist` 会失败(报错 `genie-trash failed` 或 `Some operations were aborted`)。

5. **API Key 是 XOR 弱混淆,不是安全存储**:`secret_store.py` 用 `chr(ord(c) ^ 0x5A)` 弱混淆存本地文件,仅防明文一眼泄露。**不要**把它当成安全存储来依赖,也不要把 key 写入源码、日志、配置 JSON。

6. **跨线程不能直接操作 Qt 控件**:keyboard/pystray/TaskManager 线程必须通过 `_Bridge(QObject)` 的信号槽跨线程投递到主线程,否则死锁/白屏。

7. **智谱 base_url 没有 `/v1`**:`https://open.bigmodel.cn/api/paas/v4`,与 DeepSeek(`https://api.deepseek.com`)不同。`OpenAICompatProvider` 内部会自动拼 `/chat/completions`,所以最终 URL 是 `https://open.bigmodel.cn/api/paas/v4/chat/completions`。

8. **F6 截图翻译必须用小区域,不要全屏**:全屏截图聊天框小字看不清,识别率低。引导用户用 F9 只框住聊天框那一条。

9. **`config.json` 用户实例会覆盖 `default_config.json`**:改默认配置不等于改用户配置。需要让用户在设置页改或直接编辑 `AppData/Roaming/LoLChatTranslator/config.json`。

10. **`.gitignore` 已忽略 `dist/` 和 `build/`**:release exe 走 GitHub Release 上传,**不要**把 exe 加进 git commit。

---

## 11. 未来可优化方向

1. **lol_clipboard 剪贴板恢复方案**:目前自动注入对 LoL 不一定有效。可调研 `Zeunig/lol_clipboard`(Rust 项目,声称能恢复 LoL 游戏内 Ctrl+V 粘贴能力),评估封号风险后集成。注意该项目 README 明确提醒存在潜在封号风险。

2. **TSF / ImmGenerateMessage 深度集成**:理论研究方向。通过 Text Services Framework 或 IME 消息链模拟"真实输入法组字上屏",可能让 LoL 接收注入文本。但实施复杂,且缺少 LoL 实证,目前不建议作为默认依赖。

3. **跨平台支持**:当前仅 Windows。可扩展 macOS/Linux,但 SendInput 注入、全局快捷键、托盘等系统服务需要重写。

4. **多账号 key 轮换**:支持配置多个 API key,自动切换以避免单 key 配额耗尽。

5. **本地 Ollama 视觉模型**:已预留 ollama provider(`qwen2.5vl:7b`),可深度测试本地视觉模型的识图能力,完全离线运行。

6. **截图区域自动检测**:目前用户需手动 F9 框选聊天框。可用 OpenCV 模板匹配自动检测 LoL 聊天框位置,免去手动选区域。

---

## 12. 快速上手检查清单

接手后第一次操作,按顺序执行:

- [ ] `gh auth status` — 确认 GitHub 登录正常
- [ ] `cd "C:/Users/Administrator/Desktop/github/lol-chat-translator" && git status` — 确认工作目录干净
- [ ] `git log --oneline -3` — 确认最新 commit 是 `ae31a36 v1.1.0`
- [ ] 阅读 `CHANGELOG.md` — 了解 v1.0.0 和 v1.1.0 的完整变更
- [ ] 阅读 `src/lolchattranslator/app/application.py` — 理解主控制器信号槽编排
- [ ] 阅读 `src/lolchattranslator/providers/openai_compat.py` — 理解 Provider 和双向 Prompt
- [ ] 阅读 `src/lolchattranslator/services/input_injector.py` — 理解注入逻辑和焦点陷阱
- [ ] 如需测试运行:`.venv/Scripts/python.exe main.py`
- [ ] 如需打包:参见第 8 节

---

**交接完成。本文档基于 v1.1.0 状态撰写,后续版本变更请同步更新本文档。**

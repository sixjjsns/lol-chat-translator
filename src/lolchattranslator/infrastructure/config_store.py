"""配置存储：应用数据目录、默认配置加载、JSON 配置读写（深合并）。"""
import json
import os
import sys
from copy import deepcopy
from pathlib import Path


def get_app_data_dir() -> Path:
    """应用数据目录：优先本地 AppData，避免污染项目目录。"""
    base = os.environ.get("LOL_TRANSLATOR_HOME")
    if base:
        return Path(base)
    if sys.platform == "win32":
        root = os.environ.get("APPDATA") or str(Path.home())
    else:
        root = str(Path.home())
    return Path(root) / "LoLChatTranslator"


def get_config_path() -> Path:
    return get_app_data_dir() / "config.json"


def _resource_path(rel: str) -> Path:
    """打包后资源路径（default_config.json）。"""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / rel
    # 源码运行时：项目根目录（config_store.py 在 src/lolchattranslator/infrastructure/ 下，
    # parents[3] 即项目根）
    return Path(__file__).resolve().parents[3] / rel


DEFAULT_CONFIG_PATH = _resource_path("config/default_config.json")


def _load_defaults() -> dict:
    try:
        with open(DEFAULT_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _deep_merge(base: dict, override: dict) -> dict:
    """递归合并，override 优先。"""
    result = deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


class ConfigStore:
    """配置读写，带默认值合并与内存缓存。"""

    def __init__(self, config_path: Path = None):
        self.config_path = config_path or get_config_path()
        self._defaults = _load_defaults()
        self._data = self._load()
        self._migrate()

    def _migrate(self) -> None:
        """配置迁移：把旧版本固化的配置值升级到新默认值（幂等）。

        背景：用户本地 config.json 一旦保存过，就会覆盖 default_config.json 的新默认值。
        这里对已知的"旧值需要强制升级"的键做自动修正，避免新版本默认值不生效。
        """
        changed = False
        # image_detail: low -> high（low 会把截图降到 512×512，导致聊天文字糊、检测不到）
        if self._data.get("api", {}).get("image_detail") == "low":
            self._data.setdefault("api", {})["image_detail"] = "high"
            changed = True
        # max_tokens: 2048 -> 512（游戏聊天翻译一两句就够，过大拖慢生成）
        if self._data.get("api", {}).get("max_tokens") == 2048:
            self._data.setdefault("api", {})["max_tokens"] = 512
            changed = True
        # 清理已废弃的快捷键动作 toggle_overlay（历史残留，与 toggle_window 冲突）
        hotkeys = self._data.get("hotkeys")
        if hotkeys and "toggle_overlay" in hotkeys:
            hotkeys.pop("toggle_overlay", None)
            changed = True
        if changed:
            try:
                self.save()
            except Exception:
                pass

    def _load(self) -> dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, encoding="utf-8") as f:
                    user = json.load(f)
                return _deep_merge(self._defaults, user)
            except Exception:
                return deepcopy(self._defaults)
        return deepcopy(self._defaults)

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        """点号路径取值，如 'api.model'。"""
        node = self._data
        for part in key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def set(self, key: str, value) -> None:
        parts = key.split(".")
        node = self._data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def reload(self) -> None:
        self._data = self._load()

    @property
    def data(self) -> dict:
        return self._data

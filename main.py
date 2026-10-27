"""LoL Chat Translator 入口（项目根目录）。

用法：
    python main.py
"""
import sys
from pathlib import Path

# 将 src 加入路径，支持直接 python main.py 运行（未安装时）
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from lolchattranslator.app.bootstrap import bootstrap  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(bootstrap())

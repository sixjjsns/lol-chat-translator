"""LoL Chat Translator 启动入口。

用法：
    python -m lolchattranslator
"""
from lolchattranslator.app.bootstrap import bootstrap

if __name__ == "__main__":
    raise SystemExit(bootstrap())

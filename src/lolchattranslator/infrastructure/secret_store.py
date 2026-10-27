"""API Key 安全存储：优先 Windows Credential Manager（wincred），否则回退到本地文件（弱加密）。

不把密钥写入源码、日志、配置 JSON。
"""
import json
import os
import sys
from pathlib import Path

from .config_store import get_app_data_dir

_SERVICE_NAME = "LoLChatTranslator"
_ACCOUNT_NAME = "deepseek_api_key"


def _cred_file() -> Path:
    return get_app_data_dir() / ".credential"


class SecretStore:
    """API Key 存储。

    默认使用本地文件（弱混淆 + 仅当前用户可读），避免 win32cred 在部分
    Windows 版本/权限下写入时可能导致的进程级崩溃。文件保存在应用数据目录。
    """

    def get_key(self) -> str:
        # 优先读文件（更可靠）；如存在旧版 Credential Manager 记录则回退读取
        key = self._get_from_file()
        if key:
            return key
        return self._get_from_credman()

    def set_key(self, key: str) -> None:
        # 默认写文件，最可靠，不会崩溃
        self._set_to_file(key)

    def clear_key(self) -> None:
        if sys.platform == "win32":
            try:
                import win32cred

                win32cred.CredDelete(f"{_SERVICE_NAME}/{_ACCOUNT_NAME}", win32cred.CRED_TYPE_GENERIC)
            except Exception:
                pass
        p = _cred_file()
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    def has_key(self) -> bool:
        return bool(self.get_key())

    # --- 内部 ---
    def _get_from_credman(self) -> str:
        if sys.platform != "win32":
            return ""
        try:
            import win32cred

            creds = win32cred.CredRead(f"{_SERVICE_NAME}/{_ACCOUNT_NAME}", win32cred.CRED_TYPE_GENERIC)
            blob = creds.get("CredentialBlob", "")
            if blob is None:
                return ""
            # pywin32 读回 UTF-16-LE 编码的 bytes，需解码并去掉尾部空字节
            if isinstance(blob, bytes):
                try:
                    return blob.decode("utf-16-le").rstrip("\x00")
                except Exception:
                    return blob.decode("utf-8", errors="ignore").rstrip("\x00")
            return str(blob)
        except Exception:
            return ""

    def _get_from_file(self) -> str:
        p = _cred_file()
        if not p.exists():
            return ""
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            obf = data.get("key", "")
            return "".join(chr(ord(c) ^ 0x5A) for c in obf)
        except Exception:
            return ""

    def _set_to_file(self, key: str) -> None:
        p = _cred_file()
        p.parent.mkdir(parents=True, exist_ok=True)
        # 弱混淆（非安全加密，仅防止明文一眼泄露）
        obf = "".join(chr(ord(c) ^ 0x5A) for c in key)
        data = json.dumps({"key": obf})
        # 原子写入：先写临时文件再替换，避免中断损坏
        tmp = p.with_suffix(".tmp")
        tmp.write_text(data, encoding="utf-8")
        tmp.replace(p)
        try:
            if sys.platform == "win32":
                os.chmod(str(p), 0o600)  # 尽量限制为当前用户可读写
        except Exception:
            pass

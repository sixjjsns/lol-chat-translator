"""屏幕截图服务：用 mss 截取指定矩形区域，返回 PNG 字节。"""
import time

from ..infrastructure.logging_config import get_logger

logger = get_logger()


class ScreenshotError(Exception):
    pass


class ScreenshotService:
    def __init__(self):
        self._mss = None
        self.last_duration_ms = 0.0

    def _get_mss(self):
        if self._mss is None:
            try:
                import mss

                self._mss = mss.mss()
            except ImportError as e:
                raise ScreenshotError("mss 未安装，请先 pip install -r requirements.txt") from e
        return self._mss

    def capture_region(self, region: dict) -> bytes:
        """region: {'left','top','width','height'}，返回 PNG 字节。"""
        if not region or region.get("width", 0) <= 0 or region.get("height", 0) <= 0:
            raise ScreenshotError("截图区域无效或为空，请先按 F9 选择聊天区域")

        start = time.perf_counter()
        mss = self._get_mss()
        try:
            shot = mss.grab(region)
            from PIL import Image

            img = Image.frombytes("RGB", shot.size, shot.rgb)
            import io

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            self.last_duration_ms = (time.perf_counter() - start) * 1000
            return buf.getvalue()
        except Exception as e:
            logger.warning("截图失败: %s", e)
            raise ScreenshotError(f"截图失败: {e}") from e

    def capture_to_png(self, region: dict) -> bytes:
        return self.capture_region(region)

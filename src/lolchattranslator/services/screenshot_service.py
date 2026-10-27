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
        """region: {'left','top','width','height'}，返回 PNG 字节。

        为提高小字聊天框的 OCR 识别率，截图后若区域较小会放大（upscale）
        到合适尺寸再送模型。放大会让小字更清晰，但也会增大图片体积，
        所以只在长宽较小（聊天框局部）时放大，全屏截图则不放大。
        """
        if not region or region.get("width", 0) <= 0 or region.get("height", 0) <= 0:
            raise ScreenshotError("截图区域无效或为空，请先按 F9 选择聊天区域")

        start = time.perf_counter()
        mss = self._get_mss()
        try:
            shot = mss.grab(region)
            from PIL import Image

            img = Image.frombytes("RGB", shot.size, shot.rgb)

            # 小字放大：聊天框局部截图（宽或高较小）时放大，提升 OCR 识别率
            img = self._maybe_upscale(img)

            import io

            buf = io.BytesIO()
            img.save(buf, format="PNG")
            self.last_duration_ms = (time.perf_counter() - start) * 1000
            return buf.getvalue()
        except Exception as e:
            logger.warning("截图失败: %s", e)
            raise ScreenshotError(f"截图失败: {e}") from e

    @staticmethod
    def _maybe_upscale(img) -> "Image.Image":
        """若截图较小（聊天框局部），用 LANCZOS 放大 2 倍以提升小字识别率。

        全屏截图（宽或高较大）不做放大，避免图片过大拖慢上传/识别。
        """
        w, h = img.size
        # 短边小于 400px 视为"局部截图"（聊天框通常很窄/很矮），放大
        if min(w, h) < 400:
            from PIL import Image as _Image

            img = img.resize((w * 2, h * 2), _Image.Resampling.LANCZOS)
            logger.info("截图已放大 2 倍（%dx%d -> %dx%d）以提升小字识别率", w, h, w * 2, h * 2)
        return img

    def capture_to_png(self, region: dict) -> bytes:
        return self.capture_region(region)

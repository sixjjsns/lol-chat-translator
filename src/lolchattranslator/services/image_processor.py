"""图像处理：面向"小字聊天框"的可读性增强，再编码成 data URL。

v1.2.3 重写
-----------
旧版只做「不超过 1600px 就 JPEG q85 直接发」，对游戏内聊天框这种**小字号、
高对比、细笔画**的画面很不友好：经过 JPEG 压缩后笔画边缘出现振铃，模型 OCR 更容易认错。

现在的处理顺序：

1. **短边不足 900px 就先放大**（最多 3 倍，LANCZOS）——小字放大是最有效的 OCR 增益；
2. **锐化 + 轻微提对比**（UnsharpMask + Contrast 1.12）——把白色文字从半透明聊天底板上"拔"出来；
3. **小图用 PNG 无损编码**（像素数 ≤ 220 万），大图才退回 JPEG q92——避免压缩伪影；
4. 最后再按 `max_dimension` 兜底缩放，防止上传过大。
"""

from __future__ import annotations

import base64
import io

from PIL import Image, ImageEnhance, ImageFilter

# 短边低于这个值就认为"字太小"，需要放大
MIN_SHORT_SIDE = 900
# 放大倍数上限（再大只是浪费 token）
MAX_UPSCALE = 3.0
# 小于这个像素数用 PNG（无损），超过用 JPEG
PNG_PIXEL_LIMIT = 2_200_000


class ImageProcessor:
    def __init__(self, max_dimension: int = 1600, jpeg_quality: int = 92, enhance: bool = True):
        self.max_dimension = max_dimension
        self.jpeg_quality = jpeg_quality
        self.enhance = enhance

    def process(self, png_bytes: bytes, max_dimension: int | None = None,
                jpeg_quality: int | None = None) -> str:
        """输入 PNG 字节，输出 base64 data URL（小图 PNG / 大图 JPEG）。"""
        img = Image.open(io.BytesIO(png_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")

        max_dim = max_dimension or self.max_dimension
        quality = jpeg_quality if jpeg_quality is not None else self.jpeg_quality

        img = self._upscale_small(img)
        if self.enhance:
            img = self._sharpen(img)
        img = self._fit(img, max_dim)
        return self._encode(img, quality)

    # ------------------------------------------------------------------
    @staticmethod
    def _upscale_small(img: Image.Image) -> Image.Image:
        """短边不足 MIN_SHORT_SIDE 时按比例放大，最多 MAX_UPSCALE 倍。"""
        short = min(img.size)
        if short <= 0 or short >= MIN_SHORT_SIDE:
            return img
        factor = min(MAX_UPSCALE, MIN_SHORT_SIDE / float(short))
        if factor <= 1.15:
            return img
        new_size = (max(1, int(img.width * factor)), max(1, int(img.height * factor)))
        return img.resize(new_size, Image.Resampling.LANCZOS)

    @staticmethod
    def _sharpen(img: Image.Image) -> Image.Image:
        """锐化 + 轻微提对比：让细笔画在小尺寸下也更结实。"""
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        return ImageEnhance.Contrast(img).enhance(1.12)

    def _fit(self, img: Image.Image, max_dim: int) -> Image.Image:
        if max(img.size) <= max_dim:
            return img
        ratio = max_dim / float(max(img.size))
        new_size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
        return img.resize(new_size, Image.Resampling.LANCZOS)

    def _encode(self, img: Image.Image, quality: int) -> str:
        buf = io.BytesIO()
        if img.width * img.height <= PNG_PIXEL_LIMIT:
            img.save(buf, format="PNG", optimize=True)
            mime = "png"
        else:
            img.save(buf, format="JPEG", quality=max(70, min(95, quality)), optimize=True)
            mime = "jpeg"
        data = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/{mime};base64,{data}"

    @staticmethod
    def png_to_base64(png_bytes: bytes) -> str:
        data = base64.b64encode(png_bytes).decode("ascii")
        return f"data:image/png;base64,{data}"

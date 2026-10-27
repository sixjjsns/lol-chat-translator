"""图像处理：缩放、压缩、转 Base64 data URL，兼顾可读性与体积。"""
import base64
import io

from PIL import Image


class ImageProcessor:
    def __init__(self, max_dimension: int = 1600, jpeg_quality: int = 85):
        self.max_dimension = max_dimension
        self.jpeg_quality = jpeg_quality

    def process(self, png_bytes: bytes, max_dimension: int | None = None,
                jpeg_quality: int | None = None) -> str:
        """输入 PNG 字节，输出 base64 data URL（JPEG 压缩）。"""
        img = Image.open(io.BytesIO(png_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")

        max_dim = max_dimension or self.max_dimension
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            new_size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
            img = img.resize(new_size, Image.LANCZOS)

        quality = jpeg_quality if jpeg_quality is not None else self.jpeg_quality
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        data = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{data}"

    @staticmethod
    def png_to_base64(png_bytes: bytes) -> str:
        data = base64.b64encode(png_bytes).decode("ascii")
        return f"data:image/png;base64,{data}"

from enum import Enum


class HosterEnum(Enum):
    """Перечисление доступных хостов для скачивания"""

    INSTAGRAM = "INSTAGRAM"
    TIKTOK = "TIKTOK"


class ExtPhotoEnum(Enum):
    """Перечисление доступных форматов изображений"""

    JPG = ".jpeg"
    JPEG = ".jpg"
    PNG = ".png"
    WEBP = ".webp"
    GIF = ".gif"
    SVG = ".svg"
    TIFF = ".tiff"


class ExtVideoEnum(Enum):
    """Перечисление доступных форматов видео"""

    WEBM = ".webm"
    MP4 = ".mp4"
    MOV = ".mov"

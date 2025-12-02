"""Модуль с дополнительным функциями"""
import logging
import shutil
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

from enums import HosterEnum

logger = logging.getLogger(__name__)


def rm_tree(path: Path) -> None:
    """Удалить директорию и все содержимое

    Args:
        path: путь к удаляемой директории.
    """
    try:
        for item in path.iterdir():
            if item.is_file() or item.is_symlink():
                logging.debug(f"Удаляем файл {item}")
                item.unlink(missing_ok=True)
            elif item.is_dir():
                logging.debug(f"Удаляем папку {item}")
                shutil.rmtree(item)

    except FileNotFoundError:
        logger.debug('Папка или файл уже отсутствует')


def cut_query(url: str) -> str:
    """Срезает все лишние query-параметры, учитывая ?next=

    Args:
        url: ссылка

    Returns:
        Очищенная ссылка без query-параметров
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    if "next" in query_params:
        next_url = unquote(query_params["next"][0])
        return cut_query(next_url)

    return parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path


def get_cookies(content_type: HosterEnum | None):
    if content_type == HosterEnum.INSTAGRAM:
        cookies = ["--cookies", str(Path("cookies","instagram_cookies.txt"))]

    elif content_type == HosterEnum.TIKTOK:
        cookies = ["--cookies", str(Path("cookies", "tiktok_cookies.txt"))]

    elif content_type == HosterEnum.VK:
        cookies = ["--cookies", str(Path("cookies", "vk_cookies.txt"))]

    else:
        cookies = []

    return cookies


def get_subprocess_args(content_type: HosterEnum | None, url: str, download_path: Path) -> list[str]:
    if content_type  in [HosterEnum.YOUTUBE, HosterEnum.VK, HosterEnum.PIKABU]:
        return [
            "yt-dlp",
            "-o",
            "downloads/%(title)s.%(ext)s",
            "-f",
            "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
            *get_cookies(content_type=content_type),
            url
        ]
    else:
        return ["gallery-dl", "-d", str(download_path), *get_cookies(content_type=content_type), url]

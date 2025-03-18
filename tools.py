"""Модуль с дополнительным функциями"""
import logging
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

logger = logging.getLogger(__name__)


def rm_tree(path: Path) -> None:
    """Удалить директорию и все содержимое

    Args:
        path: путь к удаляемой директории.
    """
    try:
        for child in path.iterdir():
            if child.is_file():
                child.unlink()
            else:
                rm_tree(child)
        path.rmdir()

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
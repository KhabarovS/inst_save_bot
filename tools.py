"""Модуль с дополнительным функциями"""
import logging
from pathlib import Path


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
    """Срезать все лишние квери параметры

    Args:
        url: ссылка
    """

    return url[:url.find('?')] if url.find('?') != -1 else url
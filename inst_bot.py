"""Модуль основного скрипта для загрузки видео и фото из Instagram"""

import asyncio
import logging
import os
import re
import subprocess
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session import aiohttp
from aiogram.enums import ParseMode
from aiogram.types import Message, FSInputFile

from enums import HosterEnum, ExtPhotoEnum, ExtVideoEnum
from tools import rm_tree, cut_query, get_subprocess_args

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.FileHandler("bot.log", encoding="utf-8"), logging.StreamHandler()],
)
logging.getLogger("aiogram").setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден!")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

INSTAGRAM_REGEX = r"(https?://www\.instagram\.com/[^\s]+)"
TIKTOK_REGEX = r"https?://(?:www\.)?(?:tiktok\.com/.*/video/(\d+)|vt\.tiktok\.com/\w+/?)"
YOUTUBE_REGEX = r"https?:\/\/(?:www\.)?youtube\.com\/shorts\/[^\s]+"
VK_REGEX = r"https?:\/\/(?:www\.)?(?:vk\.com\/clip-[0-9_]+|vkvideo\.ru\/video[0-9_]+)(?:\?[^\s]*)?"
PIKABU_REGEX = r"https?:\/\/(?:www\.)?pikabu\.ru\/story\/[^\s/]+_\d+"

DOWNLOAD_PATH = Path("downloads")
DOWNLOAD_PATH.mkdir(exist_ok=True)


async def get_real_url(short_url: str) -> str:
    """Получить реальную ссылку после редиректов

    Args:
        short_url: ссылка на контент
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url=short_url, allow_redirects=True) as response:
            return str(response.url)


async def download_content(url: str, content_type: HosterEnum | None) -> list[Path]:
    """Скачать контент

    Args:
        url: ссылка на контент
        content_type: тип контента
    """
    logger.debug(f"Запускаем команду для скачивания, {content_type=}")

    args = get_subprocess_args(content_type=content_type, url=url, download_path=DOWNLOAD_PATH)

    logging.debug(f"Финальная строка запуска: {" ".join(args)}")

    try:
        result = subprocess.run(args, capture_output=True, check=True)

        if result.returncode != 0:
            logger.error(f"Ошибка при выполнении команды: {result.stdout}\n{result.stderr}\n")
            return []

        files = sorted(DOWNLOAD_PATH.glob("**/*"), key=lambda x: x.stat().st_ctime, reverse=True)
        logger.debug(f"Скачанные файлы: {files}")
        content = [f for f in files if f.is_file()][:2]

        logger.debug(f"Контент успешно скачан: {content}")

        return content

    except Exception as ex:
        logger.error(f"Ошибка выполнения subprocess: {ex}\n")
        return []


@dp.message()
async def handle_message(message: Message):
    """Обработать сообщение, если есть ссылка на Instagram скачать и отправить ответом как видео

    Args:
        message: объект сообщения
    """

    if message.text:
        if match := re.search(INSTAGRAM_REGEX, message.text):
            content_type = HosterEnum.INSTAGRAM

        elif match := re.search(TIKTOK_REGEX, message.text):
            content_type = HosterEnum.TIKTOK

        elif match := re.search(YOUTUBE_REGEX, message.text):
            content_type = HosterEnum.YOUTUBE

        elif match := re.search(VK_REGEX, message.text):
            content_type = HosterEnum.VK

        elif match := re.search(PIKABU_REGEX, message.text):
            content_type = HosterEnum.PIKABU

        else:
            content_type, match = None, None

        logger.debug(f"Контент тип: {content_type}")

        if match:
            logger.info(
                f"Получено новое сообщение с ссылкой на контент {content_type.value} "
                f"от {message.from_user.username} ({message.from_user.id})"
            )

            try:
                real_url = await get_real_url(short_url=match.group(0))
                logger.debug(f"Раскрытая ссылка: {real_url}")

                files = await download_content(url=cut_query(url=real_url), content_type=content_type)

                if files:
                    for file in files:
                        suffix = file.suffix.lower()

                        if suffix in ExtPhotoEnum:
                            await message.reply_photo(FSInputFile(path=file))

                        elif suffix in ExtVideoEnum:
                            await message.reply_video(FSInputFile(path=file))

                        else:
                            logger.warning(
                                f"Неизвестный формат скачанного файла: '{file}'. Попытка отправить как документ"
                            )
                            await message.reply_document(
                                FSInputFile(path=file),
                                caption=f"Данный формат файла {suffix} "
                                        "не входит в список допустимых форматов фото или видео",
                            )

                        logger.info(f"Файл {file} успешно отправлен в чат")

                else:
                    await message.reply("Что-то пошло не так при скачивании видео, увы 🍌")

            except Exception as ex:
                logger.error(f"Ошибка при отправке контента: {ex}")

            finally:
                rm_tree(path=DOWNLOAD_PATH)
                logger.info("*"* 50)


async def main():
    """Точка G"""
    logger.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except Exception as e:
        logger.exception(f"Произошла непредвиденная ошибка: {e}")

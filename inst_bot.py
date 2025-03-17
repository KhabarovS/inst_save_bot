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

from tools import rm_tree, cut_query


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("aiogram").setLevel(logging.CRITICAL)


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден!")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

INSTAGRAM_REGEX = r"(https?://www\.instagram\.com/[^\s]+)"

DOWNLOAD_PATH = Path("downloads")
DOWNLOAD_PATH.mkdir(exist_ok=True)


async def get_real_instagram_url(short_url: str) -> str:
    """Получить реальную ссылку после редиректов

    Args:
        short_url: ссылка на контент
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url=short_url, allow_redirects=True) as response:
            return str(response.url)


async def download_instagram_content(url: str) -> list[Path]:
    """Скачать контент из Instagram

    Args:
        url: ссылка на контент
    """
    logger.debug('Запускаем команду для скачивания')
    try:
        subprocess.run(
            [
                "gallery-dl",
                "--cookies", str(Path('instagram_cookies.txt')),
                "-d", str(DOWNLOAD_PATH),
                url
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        files = sorted(DOWNLOAD_PATH.glob('**/*'), key=lambda x: x.stat().st_ctime, reverse=True)
        logger.debug(f'Скачанные файлы: {files}')
        content = [f for f in files if f.is_file()][:1]

        logger.debug(f"Контент успешно скачан: {content}")

        return content

    except subprocess.CalledProcessError as ex:
        logger.error(f"Ошибка gallery-dl: {ex}")
        return []


@dp.message()
async def handle_message(message: Message):
    """Обработать сообщение, если есть ссылка на Instagram скачать и отправить ответом как видео

    Args:
        message: объект сообщения
    """

    if message.text:
        match = re.search(INSTAGRAM_REGEX, message.text)

        if match:
            logger.info(
                "Получено новое сообщение с ссылкой на видео Instagram "
                f"от {message.from_user.username} ({message.from_user.id})"
            )

            try:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text='\U0001F680 Ссылка принята, начинаю скачивание'
                )

                real_url = await get_real_instagram_url(short_url=match.group(0))
                logger.debug(f"Раскрытая ссылка: {real_url}")

                files = await download_instagram_content(url=cut_query(url=real_url))

                if files:
                    for file in files:
                        if file.suffix in ('.jpg', 'jpeg'):
                            await message.reply_photo(FSInputFile(path=file))
                        else:
                            await message.reply_document(FSInputFile(path=file))
                        logger.info(f'Файл {file} успешно отправлен в чат')
                else:
                    await message.reply("Что-то пошло не так при скачивании видео, увы \U0001F34C")

            except Exception as ex:
                logger.error(f"Ошибка при отправке контента: {ex}")

            finally:
                for p in DOWNLOAD_PATH.iterdir():
                    rm_tree(path=p)


async def main():
    """Точка G"""
    logger.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())

    except Exception as e:
        logger.exception(f"Произошла непредвиденная ошибка: {e}")

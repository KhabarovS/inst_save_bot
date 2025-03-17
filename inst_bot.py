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

from enums import HosterEnum
from tools import rm_tree, cut_query

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logging.getLogger("aiogram").setLevel(logging.CRITICAL)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден!")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

INSTAGRAM_REGEX = r"(https?://www\.instagram\.com/[^\s]+)"
TIKTOK_REGEX = r"https?://(?:www\.)?(?:tiktok\.com/.*/video/(\d+)|vt\.tiktok\.com/\w+/?)"

DOWNLOAD_PATH = Path("downloads")
DOWNLOAD_PATH.mkdir(exist_ok=True)

CONFIG = {
    HosterEnum.INSTAGRAM: {},
    HosterEnum.TIKTOK: {
        "has_spoiler": True,
        "caption": "❗ Внимание! данное видео из ТикТок! Не рекомендуется для просмотра всем Полинам в этом чате"
    }
}


async def get_real_url(short_url: str) -> str:
    """Получить реальную ссылку после редиректов

    Args:
        short_url: ссылка на контент
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url=short_url, allow_redirects=True) as response:
            return str(response.url)


async def download_content(url: str, content_type: HosterEnum) -> list[Path]:
    """Скачать контент

    Args:
        url: ссылка на контент
        content_type: тип контента
    """
    logger.debug(f'Запускаем команду для скачивания, {content_type=}')

    cookies = str(
        Path('cookies', 'instagram_cookies.txt' if content_type == HosterEnum.INSTAGRAM else 'tiktok_cookies.txt')
    )


    logger.debug(f"Выбран файл куков: {cookies}")

    try:
        subprocess.run(
            [
                "gallery-dl",
                "--cookies", cookies,
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

        if match := re.search(INSTAGRAM_REGEX, message.text):
            content_type = HosterEnum.INSTAGRAM

        elif match := re.search(TIKTOK_REGEX, message.text):
            content_type = HosterEnum.TIKTOK

        else:
            content_type, match = None, None

        logger.debug(f'Контент тип: {content_type}')

        if match:
            logger.info(
                f"Получено новое сообщение с ссылкой на контент {content_type.value} "
                f"от {message.from_user.username} ({message.from_user.id})"
            )

            try:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text='🚀 Ссылка принята, начинаю скачивание'
                )

                real_url = await get_real_url(short_url=match.group(0))
                logger.debug(f"Раскрытая ссылка: {real_url}")

                files = await download_content(url=cut_query(url=real_url), content_type=content_type)

                if files:
                    for file in files:
                        if file.suffix in ('.jpg', 'jpeg', '.png'):
                            await message.reply_photo(FSInputFile(path=file), **CONFIG.get(content_type, {}))
                        else:
                            await message.reply_video(FSInputFile(path=file), **CONFIG.get(content_type, {}))
                        logger.info(f'Файл {file} успешно отправлен в чат')
                else:
                    await message.reply("Что-то пошло не так при скачивании видео, увы 🍌")

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

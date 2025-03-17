import asyncio
import os
import re
import sys
import uuid
from pathlib import Path

import instaloader
import requests
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, FSInputFile
from loguru import logger


logger.remove()

logger.add(
    sink=sys.stdout,
    level='DEBUG',
    format='\n{time:HH:mm:ss.SSS} | <level>{level}</level> | <level>{message}</level>',
)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден!")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
L = instaloader.Instaloader(quiet=True)

INSTAGRAM_REGEX = r"(https?://www\.instagram\.com/[^\s]+)"

DOWNLOAD_PATH: Path = Path("downloads")
DOWNLOAD_PATH.mkdir(exist_ok=True)


def get_real_instagram_url(url) -> str | None:
    """Получить реальный url после всех редиректов

    Args:
        url: полученный юрл из сообщения тг
    """
    try:
        response = requests.get(url, allow_redirects=True)
        logger.debug(f'Реальный url: {response.url}')
        return response.url

    except Exception as ex:
        logger.warning(f"Error fetching real Instagram URL: {ex}")
        return None


def get_shortcode(url) -> tuple[str, str]:
    """Получить из ссылки шорткод

    Args:
        url: реальный юрл полученный после всех редиректов
    """
    if url.find('?') != -1:
        url = url[:url.find('?')]

    parts = [x for x in url.split('/') if x]

    logger.debug(f'Получили тип контента "{parts[-2]}", Шорткод: "{parts[-1]}"')

    return parts[-2], parts[-1]


def download_inst_content(content_type, shortcode) -> Path | None:
    """Получить ссылку на скачанный контент

    Args:
        content_type: тип контента
        shortcode: реальный шорткод
    """
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        content_path = (DOWNLOAD_PATH / str(uuid.uuid4()))
        content_path.mkdir(exist_ok=True)

        content_type = '.jpg' if content_type == 'p' else '.mp4'
        L.download_post(post, target=str(content_path))

        for file in content_path.glob(f'*{content_type}'):
            logger.info(f'Найденный файл через glob {file}')
            return file

    except Exception:
        return None


def get_downloaded_path(source_url) -> Path | str:
    real_url = get_real_instagram_url(url=source_url)

    if real_url is not None:
        content_type, shortcode = get_shortcode(url=real_url)

        content = download_inst_content(content_type=content_type, shortcode=shortcode)

        if content:
            return content

    return "Что-то пошло не так при скачивании контента, увы \U0001F34C"


def rm_tree(path: Path):
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


@dp.message()
async def handle_message(message: Message):
    """Обработать сообщение, если есть ссылка на Instagram скачать и отправить ответом скачанный контент

    Args:
        message: объект сообщения
    """

    if message.text:
        match = re.search(INSTAGRAM_REGEX, message.text)

        if not match:
            return

        logger.info(
            f"Получено новое сообщение с ссылкой на контент от {message.from_user.username} ({message.from_user.id})"
        )

        await bot.send_message(
            chat_id=message.chat.id,
            text='\U0001F680 Ссылка принята, начинаю скачивание'
        )

        content_path = get_downloaded_path(source_url=match.group(0))

        try:
            if isinstance(content_path, str):
                await message.reply(content_path)

            else:
                if content_path.suffix == '.mp4':
                    await message.reply_video(video=FSInputFile(path=content_path, filename=content_path.name))

                else:
                    await message.reply_photo(photo=FSInputFile(path=content_path, filename=content_path.name))

        except Exception as ex:
            logger.error(f"Ошибка при отправке контента в тг: {ex}")

        finally:
            rm_tree(path=DOWNLOAD_PATH)


async def main():
    """Точка G"""
    logger.info("Бот запускается...")
    await dp.start_polling(bot)
    logger.info("Бот начал работать")


if __name__ == '__main__':
    try:
        asyncio.run(main())

    except Exception as e:
        logger.exception(f"Произошла непредвиденная ошибка: {e}")

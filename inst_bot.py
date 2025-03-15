import asyncio
import os
import re
import subprocess
import uuid
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, FSInputFile
from loguru import logger

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN не найден!")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


INSTAGRAM_REGEX = r"(https?://www\.instagram\.com/[^\s]+)"

DOWNLOAD_PATH = Path("downloads")
DOWNLOAD_PATH.mkdir(exist_ok=True)

async def download_instagram_video(url: str) -> Path | str | None:
    """Скачать видео по ссылке на Instagram

    Args:
        url: ссылка
    """
    video_path = DOWNLOAD_PATH / f"{str(uuid.uuid4())[-12:]}.mp4"
    logger.info(f"Начало скачивания видео с URL: {url}")

    process = await asyncio.create_subprocess_exec(
        "yt-dlp", "--max-filesize", "300M", "-o", str(video_path), url,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error(f"Ошибка при скачивании видео: {stderr.decode().strip()}")
        return "Что-то пошло не так при скачивании видео, увы ¯\_(ツ)_/¯"

    logger.info(f"Видео успешно скачано: {video_path}")

    return video_path


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
                f"Получено новое сообщение с ссылкой на видео от {message.from_user.username} ({message.from_user.id})"
            )

            video_path = await download_instagram_video(url=match.group(0))

            if isinstance(video_path, str):
                await message.reply(video_path)

            elif video_path:
                try:
                    await message.reply_video(video=FSInputFile(path=video_path, filename=video_path.name))
                    logger.info(f"Видео отправлено в чат: {message.chat.id}")

                except Exception as ex:
                    logger.error(f"Ошибка при отправке видео: {ex}")

                finally:
                    video_path.unlink()


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
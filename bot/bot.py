import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv

from bot.handlers import router


load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PROXY_URL = os.getenv("TELEGRAM_PROXY")

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env")


session = AiohttpSession(proxy=PROXY_URL) if PROXY_URL else AiohttpSession()

bot = Bot(
    token=TOKEN,
    session=session,
)

dp = Dispatcher()

# Подключаем обработчики
dp.include_router(router)


async def main():
    print("🤖 StudyFlow Bot запускается...")

    me = await bot.get_me()
    print(f"✅ Подключение к Telegram успешно: @{me.username}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

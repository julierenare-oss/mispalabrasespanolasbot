import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import menu, upload, session, settings
from handlers.stats import router as stats_router

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем все роутеры
    dp.include_router(menu.router)
    dp.include_router(upload.router)
    dp.include_router(session.router)
    dp.include_router(settings.router)
    dp.include_router(stats_router)

    # Инициализируем базу данных
    await init_db()

    print("✅ Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

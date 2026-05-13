import asyncio
import threading
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from handlers import router
from admin import router as admin_router
from webhook import run_webhook

async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(admin_router)
    # Запускаем вебхук в отдельном потоке
    threading.Thread(target=run_webhook, daemon=True).start()
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

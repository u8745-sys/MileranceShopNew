import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from database import init_db
from handlers import router
from admin import router as admin_router
from webhook_handler import setup_webhook

async def start_webhook():
    app = web.Application()
    setup_webhook(app)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("Webhook server started on port 8080")

async def main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(admin_router)
    # Запускаем вебхук-сервер в фоне
    asyncio.create_task(start_webhook())
    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

BOT_TOKEN = "8664623285:AAFlvJqJOYH7jMEbY8M4MuWLiNOGFM8QKa4"

# Настройки Platima
PLATIMA_API_URL = "https://platima.ru/api/create"
PLATIMA_WEBHOOK_SECRET = "ваш_секретный_ключ"   # придумайте сложный

# ID администратора (ваш Telegram ID)
ADMIN_IDS = [123456789]  # замените на свой

# Ссылка на поддержку (ваш Telegram)
SUPPORT_LINK = "https://t.me/ваш_юзернейм"

# Каталог товаров (можно будет редактировать через админку)
# Пока что пустой, вы наполните сами через админку или вручную
CATALOG = {
    "game_currency": {
        "name": "🎮 Игровая валюта",
        "items": {}
    },
    "subscriptions": {
        "name": "📺 Подписки",
        "items": {}
    }
}

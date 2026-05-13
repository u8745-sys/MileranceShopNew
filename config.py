BOT_TOKEN = "8664623285:AAFlvJqJOYH7jMEbY8M4MuWLiNOGFM8QKa4"

# Lava.top
LAVA_SHOP_ID = "48fef41e-7f1f-4ec9-a483-8e0e362b9d1b"          # ID проекта из настроек Lava
LAVA_API_KEY = "B72ybYs31Llt4YKcaZAIB6GWjOLNwSYXLofpMfTkNrBgwjvM6WzZWEmJgAEQlA65"          # API-ключ из раздела Интеграция
LAVA_SECRET_KEY = "B72ybYs31Llt4YKcaZAIB6GWjOLNwSYXLofpMfTkNrBgwjvM6WzZWEmJgAEQlA65"    # Секретный ключ из настроек проекта
LAVA_HOOK_URL = "https://mileranceshop-production.up.railway.app/webhook/lava"
LAVA_SUCCESS_URL = "https://t.me/MileranceShop_bot"
LAVA_FAIL_URL = "https://t.me/MileranceShop_bot"

# Каталог товаров (можно редактировать через админку, но для начальной инициализации оставим)
CATALOG = {
    "fortnite": {
        "name": "🔫 Fortnite",
        "items": {
            "fn_800": {"name": "800 В-баксов", "price": 499, "desc": "На аккаунт"},
            "fn_2400": {"name": "2400 В-баксов", "price": 1299, "desc": "На аккаунт"}
        }
    },
    "subscriptions": {
        "name": "📺 Подписки",
        "items": {
            "netflix": {"name": "Netflix Premium 1 мес", "price": 1000, "desc": "4K, 4 устройства"}
        }
    }
}

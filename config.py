import os

BOT_TOKEN = "8664623285:AAFlvJqJOYH7jMEbY8M4MuWLiNOGFM8QKa4"   # от BotFather

# CryptoBot
CRYPTO_TOKEN = "582005:AA4QlZJUS4XQHveMtd8WWuSMkPyMQHrC2Op"  # ваш токен

# Начальный каталог (потом редактируется через админку)
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

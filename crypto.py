import aiohttp
from config import CRYPTO_TOKEN

API_URL = "https://pay.crypt.bot/api/createInvoice"

async def create_invoice(amount, order_id, user_id):
    """Создаёт счёт в USDT и возвращает ссылку для оплаты"""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Crypto-Pay-API-Token": CRYPTO_TOKEN,
            "Content-Type": "application/json"
        }
        payload = {
            "asset": "USDT",
            "amount": str(amount),
            "description": f"Пополнение баланса #{order_id}",
            "paid_btn_name": "callback",
            "paid_btn_url": f"https://t.me/MileranceShop_bot",   # замените на юзернейм бота
            "custom_id": order_id
        }
        async with session.post(API_URL, headers=headers, json=payload) as resp:
            data = await resp.json()
            if data.get("ok"):
                return data["result"]["bot_invoice_url"]
            else:
                print(f"[CRYPTO] Error: {data}")
                return None

import aiohttp
import hashlib
import hmac
import json
from config import LAVA_SHOP_ID, LAVA_API_KEY, LAVA_SECRET_KEY

API_URL = "https://api.lava.ru/business/invoice/create"

def generate_signature(params, secret_key):
    """Генерация подписи для Lava.top"""
    # Сортировка параметров по ключу
    sorted_params = sorted(params.items())
    sign_string = "".join([f"{k}{v}" for k, v in sorted_params])
    sign_string += secret_key
    return hashlib.sha256(sign_string.encode()).hexdigest()

async def create_invoice(amount, order_id, hook_url, success_url, fail_url, custom_fields=None):
    async with aiohttp.ClientSession() as session:
        payload = {
            "shopId": LAVA_SHOP_ID,
            "amount": amount,
            "orderId": order_id,
            "hookUrl": hook_url,
            "successUrl": success_url,
            "failUrl": fail_url,
            "expire": 60  # минут
        }
        if custom_fields:
            payload["customFields"] = custom_fields

        # Формируем подпись
        signature = generate_signature(payload, LAVA_SECRET_KEY)

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": LAVA_API_KEY,
            "X-Signature": signature
        }

        async with session.post(API_URL, headers=headers, json=payload) as resp:
            data = await resp.json()
            if data.get("status") == "success":
                return data.get("data", {}).get("url")
            else:
                print(f"Lava error: {data}")
                return None

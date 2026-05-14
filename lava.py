import aiohttp
import hashlib
import json
from config import LAVA_SHOP_ID, LAVA_API_KEY, LAVA_SECRET_KEY

API_URL = "https://api.lava.ru/business/invoice/create"

def generate_signature(params, secret_key):
    # Сортировка ключей
    sorted_keys = sorted(params.keys())
    sign_string = ""
    for key in sorted_keys:
        sign_string += f"{key}{params[key]}"
    sign_string += secret_key
    return hashlib.sha256(sign_string.encode()).hexdigest()

async def create_invoice(amount, order_id, hook_url, success_url, fail_url, custom_fields=None):
    async with aiohttp.ClientSession() as session:
        payload = {
            "shopId": LAVA_SHOP_ID,
            "sum": amount,                     # Поле "sum", а не "amount"!
            "orderId": order_id,
            "hookUrl": hook_url,
            "successUrl": success_url,
            "failUrl": fail_url,
            "expire": 60
        }
        if custom_fields:
            payload["customFields"] = custom_fields

        signature = generate_signature(payload, LAVA_SECRET_KEY)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": LAVA_API_KEY,
            "Signature": signature
        }

        async with session.post(API_URL, headers=headers, json=payload) as resp:
            text = await resp.text()
            print(f"[LAVA] Response status: {resp.status}")
            print(f"[LAVA] Response body: {text}")
            try:
                data = json.loads(text)
                if data.get("status") == "success":
                    return data.get("data", {}).get("url")
                else:
                    print(f"[LAVA] Error: {data.get('message')}")
                    return None
            except:
                print(f"[LAVA] Failed to parse JSON: {text}")
                return None
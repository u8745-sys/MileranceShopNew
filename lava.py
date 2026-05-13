# lava.py
import aiohttp
import hashlib
import hmac
import json

API_URL = 'https://api.lava.ru/business/invoice/create'
SHOP_ID = "48fef41e-7f1f-4ec9-a483-8e0e362b9d1b"
API_KEY = "B72ybYs31Llt4YKcaZAIB6GWjOLNwSYXLofpMfTkNrBgwjvM6WzZWEmJgAEQlA65"

def generate_signature(params, api_key):
    # Генерация подписи по правилам Lava.top (описаны в документации)
    data = params.copy()
    data['api_key'] = api_key
    sorted_data = dict(sorted(data.items()))
    sign_string = '|'.join([str(v) for v in sorted_data.values()])
    return hashlib.sha256(sign_string.encode()).hexdigest()

async def create_invoice(amount, order_id, hook_url, success_url, fail_url, custom_fields=None):
    async with aiohttp.ClientSession() as session:
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        payload = {
            'shopId': SHOP_ID,
            'amount': amount,
            'orderId': order_id,
            'hookUrl': hook_url,
            'successUrl': success_url,
            'failUrl': fail_url,
            'customFields': custom_fields,
            'expire': 60,  # Срок действия счета в минутах (по желанию)
        }
        # Генерируем подпись и добавляем в заголовок
        signature = generate_signature(payload, API_KEY)
        headers['Signature'] = signature

        async with session.post(API_URL, headers=headers, json=payload) as resp:
            data = await resp.json()
            if data.get('status') == 'success':
                # Возвращаем URL для оплаты
                return data.get('data', {}).get('url')
            else:
                print(f'Error: {data.get("error")}')
                return None

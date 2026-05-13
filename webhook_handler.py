from aiohttp import web
import json
import hashlib
from database import complete_deposit_order, update_balance
from config import LAVA_SECRET_KEY

async def handle_lava_webhook(request):
    try:
        # Получаем тело запроса
        body = await request.text()
        data = json.loads(body)

        # Проверяем подпись (опционально, но для безопасности)
        signature = request.headers.get("X-Signature")
        if signature:
            expected = hashlib.sha256((body + LAVA_SECRET_KEY).encode()).hexdigest()
            if signature != expected:
                return web.Response(status=403, text="Invalid signature")

        order_id = data.get("order_id")
        status = data.get("status")

        if status == "success" and order_id:
            # Зачисляем средства
            if complete_deposit_order(order_id):
                return web.Response(status=200, text="OK")
            else:
                return web.Response(status=404, text="Order not found")
        else:
            return web.Response(status=400, text="Invalid status")
    except Exception as e:
        print(f"Webhook error: {e}")
        return web.Response(status=500, text="Internal error")

def setup_webhook(app):
    app.router.add_post("/webhook/lava", handle_lava_webhook)

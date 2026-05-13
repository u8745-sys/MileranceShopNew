import hashlib
import json
from aiohttp import web
from database import complete_deposit_order
from config import PLATIMA_WEBHOOK_SECRET

async def handle_platima_webhook(request):
    body = await request.text()
    signature = request.headers.get("X-Platima-Signature")
    expected = hashlib.sha256((body + PLATIMA_WEBHOOK_SECRET).encode()).hexdigest()
    if not signature or signature != expected:
        return web.Response(status=403, text="Forbidden")

    data = json.loads(body)
    order_id = data.get("order_id")
    status = data.get("status")

    if status == "paid" and order_id:
        success = complete_deposit_order(order_id)
        if success:
            return web.Response(status=200, text="OK")
    return web.Response(status=400, text="Invalid data")

def run_webhook():
    app = web.Application()
    app.router.add_post("/webhook/platima", handle_platima_webhook)
    web.run_app(app, host="0.0.0.0", port=8080)

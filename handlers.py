import asyncio
import uuid
import aiohttp
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from config import BOT_TOKEN, PLATIMA_API_URL
from database import (
    add_user, get_user_balance, update_balance,
    add_deposit_order, complete_deposit_order,
    add_purchase, get_user_purchases,
    get_promocode, use_promo_code,
    load_catalog, save_catalog
)
from keyboards import main_menu, catalog_menu, items_menu, profile_menu, deposit_keyboard, back_to_main

router = Router()
bot = Bot(token=BOT_TOKEN)

# ========== СТАРТ ==========
@router.message(CommandStart())
async def start(message: Message):
    add_user(message.from_user.id, message.from_user.username)
    balance = get_user_balance(message.from_user.id)
    await message.answer(f"👋 Добро пожаловать в MileranceShop!\n💰 Ваш баланс: {balance} ₽", reply_markup=main_menu())

# ========== ГЛАВНОЕ МЕНЮ ==========
@router.callback_query(F.data == "main_menu")
async def back_main(call: CallbackQuery):
    balance = get_user_balance(call.from_user.id)
    await call.message.edit_text(f"👋 Главное меню\n💰 Баланс: {balance} ₽", reply_markup=main_menu())
    await call.answer()

# ========== ПРОФИЛЬ И ИСТОРИЯ ==========
@router.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    balance = get_user_balance(call.from_user.id)
    await call.message.edit_text(f"👤 Ваш профиль\n💰 Баланс: {balance} ₽", reply_markup=profile_menu())
    await call.answer()

@router.callback_query(F.data == "history")
async def history(call: CallbackQuery):
    purchases = get_user_purchases(call.from_user.id)
    if not purchases:
        text = "📭 У вас пока нет покупок."
    else:
        text = "📜 История покупок:\n"
        for p in purchases:
            text += f"• {p[1]} — {p[2]} ₽ ({p[3][:10]})\n"
    await call.message.edit_text(text, reply_markup=back_to_main())
    await call.answer()

# ========== ПОПОЛНЕНИЕ БАЛАНСА ==========
@router.callback_query(F.data == "deposit")
async def deposit_menu(call: CallbackQuery):
    await call.message.edit_text("💰 Выберите сумму пополнения:", reply_markup=deposit_keyboard())
    await call.answer()

@router.callback_query(F.data.startswith("deposit_"))
async def deposit_amount(call: CallbackQuery):
    amount = int(call.data.split("_")[1])
    user_id = call.from_user.id
    order_id = add_deposit_order(user_id, amount)

    # Генерация ссылки Platima
    async with aiohttp.ClientSession() as session:
        params = {
            "amount": amount,
            "description": f"Пополнение баланса #{order_id}",
            "order_id": order_id,
            "currency": "RUB",
            "success_url": f"https://t.me/{(await bot.get_me()).username}",
            "webhook_url": "https://mileranceshop-production.up.railway.app/webhook/platima"  # укажите ваш реальный URL
        }
        async with session.get(PLATIMA_API_URL, params=params) as resp:
            data = await resp.json()
            platima_url = data.get("url")

    if platima_url:
        await call.message.edit_text(
            f"💳 Для пополнения на {amount} ₽ перейдите по ссылке:\n{platima_url}\n\nПосле оплаты баланс обновится автоматически.",
            reply_markup=back_to_main()
        )
    else:
        await call.message.edit_text("❌ Ошибка создания платежа. Попробуйте позже.", reply_markup=back_to_main())
    await call.answer()

# ========== ПРОМОКОДЫ ==========
@router.callback_query(F.data == "promocode")
async def promocode_prompt(call: CallbackQuery):
    await call.message.answer("🎁 Введите код промокода (одним сообщением):")
    await call.answer()

@router.message()
async def apply_promocode(message: Message):
    # Если пользователь ввел промокод
    code = message.text.strip().upper()
    promo = get_promocode(code)
    if not promo:
        await message.answer("❌ Неверный или просроченный промокод.")
        return
    discount_type, discount_value = promo[1], promo[2]
    # Применяем промокод: для простоты начислим на баланс фиксированную сумму или процент от чего-то?
    # Лучше добавить логику, но пока просто сообщим
    if discount_type == "fixed":
        update_balance(message.from_user.id, discount_value)
        await message.answer(f"✅ Промокод активирован! Начислено {discount_value} ₽ на баланс.")
    else:
        await message.answer(f"🎁 Промокод активирован! Скидка {discount_value}% на следующую покупку (пока не реализовано).")
    # Отметим использование
    use_promo_code(message.from_user.id, code)

# ========== КАТАЛОГ (из JSON) ==========
@router.callback_query(F.data == "catalog")
async def show_catalog(call: CallbackQuery):
    catalog = load_catalog()
    if not catalog:
        await call.message.edit_text("Каталог пуст. Обратитесь к админу.", reply_markup=back_to_main())
        return
    # Генерируем клавиатуру из категорий
    from keyboards import catalog_keyboard
    await call.message.edit_text("Выберите категорию:", reply_markup=catalog_keyboard())
    await call.answer()

@router.callback_query(F.data.startswith("cat_"))
async def show_items(call: CallbackQuery):
    cat_id = call.data.split("_")[1]
    catalog = load_catalog()
    if cat_id not in catalog:
        await call.answer("Категория не найдена")
        return
    # Клавиатура с товарами
    from keyboards import items_keyboard
    await call.message.edit_text(f"Товары в {catalog[cat_id]['name']}:", reply_markup=items_keyboard(cat_id))
    await call.answer()

@router.callback_query(F.data.startswith("item_"))
async def show_item_detail(call: CallbackQuery):
    _, cat_id, item_id = call.data.split("_")
    catalog = load_catalog()
    if cat_id not in catalog or item_id not in catalog[cat_id]["items"]:
        await call.answer("Товар не найден")
        return
    item = catalog[cat_id]["items"][item_id]
    text = f"📦 {item['name']}\n💰 {item['price']} ₽\n📝 {item['desc']}"
    await call.message.edit_text(text, reply_markup=item_detail_keyboard(cat_id, item_id, item['price']))
    await call.answer()

@router.callback_query(F.data.startswith("buy_"))
async def buy_item(call: CallbackQuery):
    _, cat_id, item_id = call.data.split("_")
    catalog = load_catalog()
    item = catalog[cat_id]["items"][item_id]
    price = item["price"]
    user_id = call.from_user.id
    balance = get_user_balance(user_id)
    if balance >= price:
        update_balance(user_id, -price)
        add_purchase(user_id, item["name"], price)
        await call.message.answer(f"✅ Вы купили {item['name']} за {price} ₽. Спасибо за покупку!")
        await call.message.edit_reply_markup(reply_markup=None)
        await back_main(call)
    else:
        await call.answer(f"❌ Недостаточно средств. Нужно {price} ₽, у вас {balance} ₽.", show_alert=True)
    await call.answer()

# ========== ВСПОМОГАТЕЛЬНЫЕ ==========
@router.callback_query(F.data == "ignore")
async def ignore_callback(call: CallbackQuery):
    await call.answer()

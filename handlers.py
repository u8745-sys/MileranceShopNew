import uuid
import aiohttp
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart

from config import BOT_TOKEN, PLATIMA_API_URL, CATALOG
from database import (add_user, get_user_balance, update_balance, add_deposit_order,
                      complete_deposit_order, add_purchase, get_user_purchases,
                      get_promocode, use_promocode, load_catalog, save_catalog)
from keyboards import (main_menu, profile_menu, deposit_menu, catalog_menu,
                       items_menu, item_detail_menu, back_to_main)

router = Router()
bot = Bot(token=BOT_TOKEN)

# Временное хранилище для фото товаров (item_id -> file_id)
# В реальном проекте лучше хранить в БД, но для простоты так
item_photos = {}

@router.message(CommandStart())
async def cmd_start(message: Message):
    add_user(message.from_user.id, message.from_user.username)
    balance = get_user_balance(message.from_user.id)
    await message.answer(
        f"👋 Добро пожаловать в MileranceShop!\n💰 Ваш баланс: {balance} ₽",
        reply_markup=main_menu(balance)
    )

@router.callback_query(F.data == "main_menu")
async def back_main(call: CallbackQuery):
    balance = get_user_balance(call.from_user.id)
    await call.message.edit_text(
        f"👋 Главное меню\n💰 Баланс: {balance} ₽",
        reply_markup=main_menu(balance)
    )
    await call.answer()

@router.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    balance = get_user_balance(call.from_user.id)
    await call.message.edit_text(
        f"👤 Ваш профиль\n💰 Баланс: {balance} ₽",
        reply_markup=profile_menu(balance)
    )
    await call.answer()

@router.callback_query(F.data == "history")
async def purchase_history(call: CallbackQuery):
    purchases = get_user_purchases(call.from_user.id)
    if not purchases:
        text = "📭 У вас пока нет покупок."
    else:
        text = "📜 История покупок:\n\n"
        for p in purchases[:10]:
            text += f"📦 {p[1]} — {p[2]} ₽\n📅 {p[3]}\n\n"
    await call.message.edit_text(text, reply_markup=back_to_main())
    await call.answer()

@router.callback_query(F.data == "deposit")
async def deposit(call: CallbackQuery):
    await call.message.edit_text("💰 Выберите сумму пополнения:", reply_markup=deposit_menu())
    await call.answer()

@router.callback_query(F.data.startswith("deposit_"))
async def deposit_amount(call: CallbackQuery):
    amount = int(call.data.split("_")[1])
    order_id = str(uuid.uuid4())[:8]
    user_id = call.from_user.id

    # Сохраняем заказ в БД со статусом pending
    add_deposit_order(order_id, user_id, amount)

    async with aiohttp.ClientSession() as session:
        params = {
            "amount": amount,
            "description": f"Пополнение баланса #{order_id}",
            "order_id": order_id,
            "currency": "RUB",
            "success_url": f"https://t.me/{(await bot.get_me()).username}",
            "webhook_url": "https://ваш-домен.up.railway.app/webhook/platima"  # замените на реальный
        }
        async with session.get(PLATIMA_API_URL, params=params) as resp:
            data = await resp.json()
            platima_url = data.get("url")

    if platima_url:
        await call.message.edit_text(
            f"💳 Ссылка для оплаты {amount} ₽:\n{platima_url}\n\nПосле оплаты баланс пополнится автоматически.",
            reply_markup=back_to_main()
        )
    else:
        await call.message.edit_text("❌ Ошибка создания платежа. Попробуйте позже.", reply_markup=back_to_main())
    await call.answer()

@router.callback_query(F.data == "catalog")
async def show_catalog(call: CallbackQuery):
    catalog = load_catalog()
    if not catalog:
        await call.message.edit_text("📭 Каталог пуст. Скоро появятся товары!", reply_markup=back_to_main())
        await call.answer()
        return
    await call.message.edit_text("Выберите категорию:", reply_markup=catalog_menu(catalog))
    await call.answer()

@router.callback_query(F.data.startswith("cat_"))
async def show_category_items(call: CallbackQuery):
    cat_id = call.data.split("_")[1]
    catalog = load_catalog()
    if cat_id not in catalog:
        await call.answer("Категория не найдена")
        return
    category = catalog[cat_id]
    await call.message.edit_text(f"Товары в {category['name']}:", reply_markup=items_menu(cat_id, category))
    await call.answer()

@router.callback_query(F.data.startswith("item_"))
async def show_item_detail(call: CallbackQuery):
    _, cat_id, item_id = call.data.split("_")
    catalog = load_catalog()
    if cat_id not in catalog or item_id not in catalog[cat_id]["items"]:
        await call.answer("Товар не найден")
        return
    item = catalog[cat_id]["items"][item_id]
    text = f"📦 {item['name']}\n💰 {item['price']} ₽\n📝 {item.get('desc', 'Нет описания')}"

    # Отправляем фото, если есть
    photo_id = item_photos.get(item_id)
    if photo_id:
        await call.message.delete()
        await call.message.answer_photo(photo_id, caption=text, reply_markup=item_detail_menu(cat_id, item_id))
    else:
        await call.message.edit_text(text, reply_markup=item_detail_menu(cat_id, item_id))
    await call.answer()

@router.callback_query(F.data.startswith("buy_"))
async def buy_item(call: CallbackQuery):
    _, cat_id, item_id = call.data.split("_")
    catalog = load_catalog()
    if cat_id not in catalog or item_id not in catalog[cat_id]["items"]:
        await call.answer("Товар не найден")
        return
    item = catalog[cat_id]["items"][item_id]
    price = item["price"]
    user_id = call.from_user.id
    balance = get_user_balance(user_id)

    if balance >= price:
        # Списание и запись покупки
        update_balance(user_id, -price)
        add_purchase(user_id, item_id, item["name"], price)
        # Здесь можно добавить логику выдачи товара (ключ, ссылка)
        await call.answer("✅ Покупка совершена!", show_alert=True)
        await call.message.edit_text(
            f"✅ Вы купили {item['name']} за {price} ₽\n\n🎮 Товар будет выдан автоматически или с вами свяжется менеджер.",
            reply_markup=back_to_main()
        )
        # Обновляем меню (баланс изменился)
        balance_new = get_user_balance(user_id)
        await call.message.answer(f"💰 Новый баланс: {balance_new} ₽", reply_markup=main_menu(balance_new))
    else:
        await call.answer(f"❌ Недостаточно средств! Нужно {price} ₽, у вас {balance} ₽", show_alert=True)
    await call.answer()

@router.callback_query(F.data == "promocode")
async def promocode_prompt(call: CallbackQuery):
    await call.message.edit_text("🎁 Введите код промокода:\nНапишите его в чат.")
    await call.answer()

@router.message(lambda msg: msg.text and len(msg.text) < 20 and msg.text.isupper())
async def apply_promocode(message: Message):
    code = message.text.strip().upper()
    promo = get_promocode(code)
    if not promo:
        await message.answer("❌ Неверный или просроченный промокод")
        return
    discount, uses_left, expires_at = promo
    if not use_promocode(message.from_user.id, code):
        await message.answer("❌ Вы уже использовали этот промокод")
        return
    update_balance(message.from_user.id, discount)
    await message.answer(f"✅ Промокод {code} активирован! Начислено {discount} ₽ на баланс.")

import time
import sqlite3
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN
from database import (
    DB_NAME, add_user, get_user_balance, update_balance,
    add_deposit_order_with_id, add_purchase, get_user_purchases,
    get_promocode, use_promo_code, load_catalog
)
from keyboards import (
    main_menu, catalog_keyboard, items_keyboard, item_detail_keyboard,
    profile_menu, deposit_keyboard, back_to_main
)
from crypto import create_invoice   # <--- импорт из crypto

router = Router()
bot = Bot(token=BOT_TOKEN)

# ----- FSM для произвольной суммы -----
class DepositStates(StatesGroup):
    waiting_for_amount = State()

# ---------- СТАРТ ----------
@router.message(CommandStart())
async def start(message: Message):
    add_user(message.from_user.id, message.from_user.username)
    balance = get_user_balance(message.from_user.id)
    await message.answer(f"👋 Добро пожаловать в MileranceShop!\n💰 Ваш баланс: {balance} ₽", reply_markup=main_menu())

# ---------- ГЛАВНОЕ МЕНЮ ----------
@router.callback_query(F.data == "main_menu")
async def back_main(call: CallbackQuery):
    balance = get_user_balance(call.from_user.id)
    await call.message.edit_text(f"👋 Главное меню\n💰 Баланс: {balance} ₽", reply_markup=main_menu())
    await call.answer()

# ---------- ПРОФИЛЬ И ИСТОРИЯ ----------
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

# ---------- ПОПОЛНЕНИЕ БАЛАНСА ----------
@router.callback_query(F.data == "deposit")
async def deposit_menu(call: CallbackQuery):
    await call.message.edit_text("💰 Выберите сумму пополнения:", reply_markup=deposit_keyboard())
    await call.answer()

@router.callback_query(F.data.startswith("deposit_"))
async def deposit_amount(call: CallbackQuery, state: FSMContext):
    # если нажата кнопка "Другая сумма"
    if call.data == "deposit_custom":
        await call.message.edit_text("💸 Введите сумму пополнения в рублях (только число):")
        await state.set_state(DepositStates.waiting_for_amount)
        await call.answer()
        return

    # фиксированные суммы
    amount = int(call.data.split("_")[1])
    user_id = call.from_user.id
    order_id = f"dep_{user_id}_{int(time.time())}"
    add_deposit_order_with_id(order_id, user_id, amount)

    pay_url = await create_invoice(amount, order_id, user_id)

    if pay_url:
        await call.message.edit_text(
            f"💳 Пополнение на {amount} ₽\n\nСсылка для оплаты (USDT):\n{pay_url}\n\nПосле оплаты нажмите '✅ Проверить оплату' или дождитесь автоматического зачисления.",
            reply_markup=back_to_main()
        )
        # TODO: добавить кнопку "Проверить оплату"
    else:
        await call.message.edit_text("❌ Ошибка создания платежа. Попробуйте позже.", reply_markup=back_to_main())
    await call.answer()

@router.message(DepositStates.waiting_for_amount)
async def process_custom_deposit(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        if amount < 10:
            await message.answer("❌ Минимальная сумма пополнения — 10 ₽. Попробуйте снова.")
            return
        if amount > 50000:
            await message.answer("❌ Максимальная сумма пополнения — 50 000 ₽. Попробуйте снова.")
            return

        user_id = message.from_user.id
        order_id = f"dep_{user_id}_{int(time.time())}"
        add_deposit_order_with_id(order_id, user_id, amount)

        pay_url = await create_invoice(amount, order_id, user_id)

        if pay_url:
            await message.answer(
                f"💳 Пополнение на {amount} ₽\n\nСсылка для оплаты (USDT):\n{pay_url}\n\nПосле оплаты нажмите '✅ Проверить оплату' или дождитесь автоматического зачисления.",
                reply_markup=back_to_main()
            )
        else:
            await message.answer("❌ Ошибка создания платежа. Попробуйте позже.", reply_markup=back_to_main())

        await state.clear()
    except ValueError:
        await message.answer("❌ Пожалуйста, введите число (только цифры).")

# ---------- ПРОМОКОДЫ ----------
@router.message(~Command(commands=["start", "admin", "confirm", "decline"]))
async def apply_promocode(message: Message):
    code = message.text.strip().upper()
    promo = get_promocode(code)
    if not promo:
        await message.answer("❌ Неверный или просроченный промокод.")
        return
    discount_type, discount_value = promo[1], promo[2]
    if discount_type == "fixed":
        update_balance(message.from_user.id, discount_value)
        await message.answer(f"✅ Промокод активирован! Начислено {discount_value} ₽ на баланс.")
    else:
        await message.answer(f"🎁 Промокод активирован! Скидка {discount_value}% на следующую покупку.")
    use_promo_code(message.from_user.id, code)

# ---------- КАТАЛОГ ----------
@router.callback_query(F.data == "catalog")
async def show_catalog(call: CallbackQuery):
    catalog = load_catalog()
    if not catalog:
        await call.message.edit_text("Каталог пуст. Обратитесь к админу.", reply_markup=back_to_main())
        return
    await call.message.edit_text("Выберите категорию:", reply_markup=catalog_keyboard())
    await call.answer()

@router.callback_query(F.data.startswith("cat_"))
async def show_items(call: CallbackQuery):
    cat_id = call.data[4:]  # после "cat_"
    catalog = load_catalog()
    if cat_id not in catalog:
        await call.answer("Категория не найдена")
        return
    await call.message.edit_text(f"Товары в {catalog[cat_id]['name']}:", reply_markup=items_keyboard(cat_id))
    await call.answer()

@router.callback_query(F.data.startswith("item_"))
async def show_item_detail(call: CallbackQuery):
    parts = call.data.split("_", 2)
    if len(parts) != 3:
        await call.answer("Ошибка: неверный формат товара")
        return
    _, cat_id, item_id = parts
    catalog = load_catalog()
    if cat_id not in catalog or item_id not in catalog[cat_id]["items"]:
        await call.answer("Товар не найден")
        return
    item = catalog[cat_id]["items"][item_id]
    text = f"📦 {item['name']}\n💰 {item['price']} ₽\n📝 {item['desc']}"
    await call.message.edit_text(text, reply_markup=item_detail_keyboard(cat_id, item_id, item['price']))
    await call.answer()

# ---------- ПОКУПКА ТОВАРА ----------
@router.callback_query(F.data.startswith("buy_"))
async def buy_item(call: CallbackQuery):
    parts = call.data.split("_", 2)
    if len(parts) != 3:
        await call.answer("Ошибка: неверный формат покупки")
        return
    _, cat_id, item_id = parts
    catalog = load_catalog()
    if cat_id not in catalog or item_id not in catalog[cat_id]["items"]:
        await call.answer("Товар не найден")
        return
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

@router.callback_query(F.data == "ignore")
async def ignore_callback(call: CallbackQuery):
    await call.answer()

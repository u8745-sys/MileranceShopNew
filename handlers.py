from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from config import CATALOG
from database import add_user, get_balance, update_balance, add_order
from keyboards import main_menu, catalog_menu, items_menu, profile_menu

router = Router()

@router.message(CommandStart())
async def start(message: Message):
    add_user(message.from_user.id, message.from_user.username)
    balance = get_balance(message.from_user.id)
    await message.answer(f"👋 Добро пожаловать!\n💰 Баланс: {balance}₽", reply_markup=main_menu())

@router.callback_query(F.data == "main_menu")
async def back_main(call: CallbackQuery):
    balance = get_balance(call.from_user.id)
    await call.message.edit_text(f"👋 Главное меню\n💰 Баланс: {balance}₽", reply_markup=main_menu())
    await call.answer()

@router.callback_query(F.data == "catalog")
async def show_catalog(call: CallbackQuery):
    await call.message.edit_text("Выберите категорию:", reply_markup=catalog_menu())
    await call.answer()

@router.callback_query(F.data.startswith("cat_"))
async def show_items(call: CallbackQuery):
    cat_id = call.data.split("_")[1]
    if cat_id in CATALOG:
        await call.message.edit_text(f"Товары в {CATALOG[cat_id]['name']}:", reply_markup=items_menu(cat_id))
    await call.answer()

@router.callback_query(F.data.startswith("buy_"))
async def buy_item(call: CallbackQuery):
    _, cat_id, item_id = call.data.split("_")
    item = CATALOG[cat_id]["items"][item_id]
    price = item["price"]
    user_id = call.from_user.id
    balance = get_balance(user_id)
    if balance >= price:
        update_balance(user_id, -price)
        add_order(user_id, [item], price)
        await call.message.answer(f"✅ Куплено: {item['name']}\nСписано: {price}₽")
        await call.message.edit_reply_markup(reply_markup=None)
        await back_main(call)
    else:
        await call.answer(f"❌ Не хватает {price - balance}₽. Пополните баланс.", show_alert=True)
    await call.answer()

@router.callback_query(F.data == "profile")
async def profile(call: CallbackQuery):
    balance = get_balance(call.from_user.id)
    await call.message.edit_text(f"👤 Ваш профиль\n💰 Баланс: {balance}₽", reply_markup=profile_menu())
    await call.answer()

@router.callback_query(F.data == "deposit")
async def deposit(call: CallbackQuery):
    await call.message.edit_text("💳 Функция пополнения через Platima будет добавлена. Пока напишите админу.")
    await call.answer()

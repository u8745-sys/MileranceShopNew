import csv
import io
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from database import update_balance, get_user_balance, add_promocode, load_catalog, save_catalog
from keyboards import back_to_main

router = Router()

# Состояния для добавления товара
class AddProductStates(StatesGroup):
    waiting_category = State()
    waiting_item_id = State()
    waiting_name = State()
    waiting_price = State()
    waiting_desc = State()
    waiting_photo = State()

# Состояния для добавления промокода
class AddPromoStates(StatesGroup):
    waiting_code = State()
    waiting_discount = State()
    waiting_uses = State()
    waiting_expiry = State()

def is_admin(user_id):
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Нет доступа")
        return
    await message.answer(
        "🔧 Админ-панель\n\n"
        "/add_balance <user_id> <сумма> — начислить баланс\n"
        "/add_product — добавить товар (пошагово)\n"
        "/add_promo — добавить промокод\n"
        "/catalog_stats — статистика каталога\n"
        "/users — выгрузка пользователей (CSV)"
    )

@router.message(Command("add_balance"))
async def add_balance_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return
    try:
        _, user_id, amount = message.text.split()
        user_id = int(user_id)
        amount = int(amount)
        update_balance(user_id, amount)
        await message.answer(f"✅ Пользователю {user_id} начислено {amount} ₽")
        await bot.send_message(user_id, f"💰 Ваш баланс пополнен на {amount} ₽ администратором.")
    except:
        await message.answer("❌ Формат: /add_balance <user_id> <сумма>")

@router.message(Command("add_product"))
async def add_product_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("➕ **Добавление товара**\nВведите **ID категории** (латиница, без пробелов):")
    await state.set_state(AddProductStates.waiting_category)

@router.message(AddProductStates.waiting_category)
async def add_category(message: Message, state: FSMContext):
    cat_id = message.text.strip()
    if " " in cat_id:
        await message.answer("❌ Без пробелов. Попробуйте снова:")
        return
    await state.update_data(category=cat_id)
    await message.answer("Введите **item_id** товара (уникальный, латиница):")
    await state.set_state(AddProductStates.waiting_item_id)

@router.message(AddProductStates.waiting_item_id)
async def add_item_id(message: Message, state: FSMContext):
    item_id = message.text.strip()
    if " " in item_id:
        await message.answer("❌ Без пробелов:")
        return
    await state.update_data(item_id=item_id)
    await message.answer("Введите **название** товара:")
    await state.set_state(AddProductStates.waiting_name)

@router.message(AddProductStates.waiting_name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Введите **цену** в рублях (только число):")
    await state.set_state(AddProductStates.waiting_price)

@router.message(AddProductStates.waiting_price)
async def add_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        await state.update_data(price=price)
        await message.answer("Введите **описание** товара (кратко):")
        await state.set_state(AddProductStates.waiting_desc)
    except:
        await message.answer("❌ Нужно число. Попробуйте:")

@router.message(AddProductStates.waiting_desc)
async def add_desc(message: Message, state: FSMContext):
    await state.update_data(desc=message.text.strip())
    await message.answer("📸 Теперь отправьте **фото** товара (можно одно). Если фото не нужно, нажмите /skip")
    await state.set_state(AddProductStates.waiting_photo)

@router.message(AddProductStates.waiting_photo, F.photo)
async def add_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.update_data(photo=photo_id)
    # Сохраняем товар в каталог
    catalog = load_catalog()
    cat_id = data['category']
    if cat_id not in catalog:
        catalog[cat_id] = {"name": cat_id, "items": {}}
    catalog[cat_id]["items"][data['item_id']] = {
        "name": data['name'],
        "price": data['price'],
        "desc": data['desc']
    }
    save_catalog(catalog)
    # Сохраняем фото в глобальный словарь (или в БД)
    from handlers import item_photos
    item_photos[data['item_id']] = photo_id
    await message.answer(f"✅ Товар добавлен!\n{data['name']} — {data['price']} ₽")
    await state.clear()

@router.message(AddProductStates.waiting_photo, Command("skip"))
async def skip_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    catalog = load_catalog()
    cat_id = data['category']
    if cat_id not in catalog:
        catalog[cat_id] = {"name": cat_id, "items": {}}
    catalog[cat_id]["items"][data['item_id']] = {
        "name": data['name'],
        "price": data['price'],
        "desc": data['desc']
    }
    save_catalog(catalog)
    await message.answer(f"✅ Товар добавлен без фото.\n{data['name']} — {data['price']} ₽")
    await state.clear()

@router.message(Command("add_promo"))
async def add_promo_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("🎁 **Добавление промокода**\nВведите код (латиница, цифры):")
    await state.set_state(AddPromoStates.waiting_code)

@router.message(AddPromoStates.waiting_code)
async def add_promo_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.update_data(code=code)
    await message.answer("Введите сумму начисления (в рублях):")
    await state.set_state(AddPromoStates.waiting_discount)

@router.message(AddPromoStates.waiting_discount)
async def add_promo_discount(message: Message, state: FSMContext):
    try:
        discount = int(message.text.strip())
        await state.update_data(discount=discount)
        await message.answer("Введите количество использований (например, 1 или 100):")
        await state.set_state(AddPromoStates.waiting_uses)
    except:
        await message.answer("❌ Введите число:")

@router.message(AddPromoStates.waiting_uses)
async def add_promo_uses(message: Message, state: FSMContext):
    try:
        uses = int(message.text.strip())
        await state.update_data(uses=uses)
        await message.answer("Введите дату окончания в формате ГГГГ-ММ-ДД (или 0 для бессрочного):")
        await state.set_state(AddPromoStates.waiting_expiry)
    except:
        await message.answer("❌ Введите число:")

@router.message(AddPromoStates.waiting_expiry)
async def add_promo_expiry(message: Message, state: FSMContext):
    text = message.text.strip()
    if text == "0":
        expiry = None
    else:
        expiry = text
    data = await state.get_data()
    add_promocode(data['code'], data['discount'], data['uses'], expiry)
    await message.answer(f"✅ Промокод {data['code']} добавлен! Начисление: {data['discount']} ₽, использований: {data['uses']}")
    await state.clear()

@router.message(Command("catalog_stats"))
async def catalog_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    catalog = load_catalog()
    if not catalog:
        await message.answer("📭 Каталог пуст")
        return
    text = "📊 Статистика каталога:\n\n"
    for cat_id, cat_data in catalog.items():
        text += f"📁 {cat_data['name']} — {len(cat_data['items'])} товаров\n"
    await message.answer(text)

@router.message(Command("users"))
async def export_users(message: Message):
    if not is_admin(message.from_user.id):
        return
    import sqlite3
    from database import DB_NAME
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, balance, registered_at FROM users")
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        await message.answer("Нет пользователей")
        return
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["User ID", "Username", "Balance", "Registered"])
    writer.writerows(rows)
    output.seek(0)
    file_path = f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(output.getvalue())
    await message.answer_document(FSInputFile(file_path), caption="📋 Список пользователей")
    import os
    os.remove(file_path)

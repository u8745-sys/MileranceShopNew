import asyncio
import csv
import io
import os
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_all_users, get_all_orders, update_order_status,
    add_product_to_db, remove_product_from_db, get_all_products,
    get_stats, get_order_by_id, get_pending_orders_count, update_balance
)
from keyboards import admin_main_menu, admin_back_button, admin_orders_menu, admin_products_menu

ADMIN_IDS = [123456789]  # ЗАМЕНИТЕ НА ВАШ TELEGRAM ID

router = Router()

# FSM для добавления товара
class AddProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_item_id = State()
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_desc = State()

# FSM для удаления товара
class DelProductStates(StatesGroup):
    waiting_for_item_id = State()

# FSM для добавления баланса пользователю
class AddBalanceStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ----- Уведомление админу о новом заказе (вызывается из handlers) -----
async def notify_admin_new_order(bot: Bot, order_id: str, user_id: int, total: int):
    for admin_id in ADMIN_IDS:
        try:
            text = (f"🆕 **Новый заказ!**\n📦 №: `{order_id}`\n👤 Пользователь: `{user_id}`\n"
                    f"💰 Сумма: `{total}` ₽\nПодтвердить: `/confirm {order_id}`\nОтклонить: `/decline {order_id}`")
            await bot.send_message(admin_id, text, parse_mode="Markdown")
        except:
            pass

# ----- АДМИН ПАНЕЛЬ -----
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа.")
        return
    pending = get_pending_orders_count()
    await message.answer(f"🔧 Админ-панель\n⏳ Ожидают подтверждения: {pending}", reply_markup=admin_main_menu())

# ----- ОБРАБОТЧИКИ КНОПОК -----
@router.callback_query(F.data.startswith("admin_"))
async def admin_callback(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Доступ запрещён", show_alert=True)
        return

    action = call.data.split("_")[1]

    if action == "stats":
        stats = get_stats()
        text = (f"📊 Статистика:\n👥 Пользователей: {stats['users']}\n📦 Заказов: {stats['total_orders']}\n"
                f"✅ Завершённых: {stats['completed_orders']}\n💰 Выручка: {stats['total_amount']}₽\n"
                f"⏳ В обработке: {stats['pending_orders']}")
        await call.message.edit_text(text, reply_markup=admin_back_button())
        await call.answer()

    elif action == "users":
        users = get_all_users()
        if not users:
            await call.message.edit_text("Нет пользователей", reply_markup=admin_back_button())
            return
        # CSV экспорт
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Username", "Баланс", "Зарегистрирован"])
        for u in users:
            writer.writerow([u[0], u[1] or "нет", u[2], u[3]])
        output.seek(0)
        file_path = f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(output.getvalue())
        await call.message.answer_document(FSInputFile(file_path), caption="📋 Список пользователей")
        os.remove(file_path)
        await call.message.edit_text("✅ Файл отправлен", reply_markup=admin_back_button())
        await call.answer()

    elif action == "orders":
        orders = get_all_orders()
        if not orders:
            await call.message.edit_text("Нет заказов", reply_markup=admin_back_button())
            return
        text = "📦 Последние 20 заказов:\n\n"
        for o in orders[:20]:
            text += f"#{o[0]} | {o[3]}₽ | {o[4]} | {o[5][:10]}\n"
        await call.message.edit_text(text, reply_markup=admin_orders_menu())
        await call.answer()

    elif action == "products":
        products = get_all_products()
        if products:
            prod_text = "📋 Текущие товары (item_id):\n"
            for cat_id, cat_data in products.items():
                prod_text += f"\n📁 {cat_id}:\n"
                for item_id, item in cat_data['items'].items():
                    prod_text += f"  • `{item_id}` — {item['name']} — {item['price']}₽\n"
            await call.message.edit_text(prod_text, reply_markup=admin_products_menu(), parse_mode="Markdown")
        else:
            await call.message.edit_text("Каталог пуст", reply_markup=admin_products_menu())
        await call.answer()

    elif action == "add_product":
        await call.message.edit_text("➕ **Добавление товара**\nВведите **ID категории** (латиница, без пробелов):")
        await state.set_state(AddProductStates.waiting_for_category)
        await call.answer()

    elif action == "del_product":
        await call.message.edit_text("❌ **Удаление товара**\nВведите **item_id** товара (например `v_bucks_1000`):")
        await state.set_state(DelProductStates.waiting_for_item_id)
        await call.answer()

    elif action == "add_balance":
        await call.message.edit_text("💰 **Добавление баланса пользователю**\nВведите **user_id** (число):")
        await state.set_state(AddBalanceStates.waiting_for_user_id)
        await call.answer()

    elif action == "broadcast":
        await call.message.edit_text("📢 Введите сообщение для рассылки (можно с фото/файлом):")
        await state.set_state("waiting_for_broadcast")
        await call.answer()

    elif action == "back":
        pending = get_pending_orders_count()
        await call.message.edit_text(f"🔧 Админ-панель\n⏳ Ожидают подтверждения: {pending}", reply_markup=admin_main_menu())
        await call.answer()

# ----- ДОБАВЛЕНИЕ ТОВАРА (шаги) -----
@router.message(AddProductStates.waiting_for_category)
async def add_product_category(message: Message, state: FSMContext):
    category_id = message.text.strip()
    if " " in category_id:
        await message.answer("❌ ID категории без пробелов. Попробуйте снова:")
        return
    await state.update_data(category_id=category_id)
    await message.answer("Введите **item_id** товара (латиница, уникальный, например `v_bucks_1000`):")
    await state.set_state(AddProductStates.waiting_for_item_id)

@router.message(AddProductStates.waiting_for_item_id)
async def add_product_item_id(message: Message, state: FSMContext):
    item_id = message.text.strip()
    if " " in item_id:
        await message.answer("❌ item_id без пробелов.")
        return
    await state.update_data(item_id=item_id)
    await message.answer("Введите **название** товара:")
    await state.set_state(AddProductStates.waiting_for_name)

@router.message(AddProductStates.waiting_for_name)
async def add_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Введите **цену** в рублях (только число):")
    await state.set_state(AddProductStates.waiting_for_price)

@router.message(AddProductStates.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext):
    try:
        price = int(message.text.strip())
        await state.update_data(price=price)
        await message.answer("Введите **описание** товара:")
        await state.set_state(AddProductStates.waiting_for_desc)
    except ValueError:
        await message.answer("❌ Введите число")

@router.message(AddProductStates.waiting_for_desc)
async def add_product_desc(message: Message, state: FSMContext):
    data = await state.update_data(desc=message.text.strip())
    success = add_product_to_db(data['category_id'], data['item_id'], data['name'], data['price'], data['desc'])
    if success:
        await message.answer(f"✅ Товар добавлен!\n{data['category_id']}/{data['item_id']} — {data['name']} — {data['price']}₽")
    else:
        await message.answer("❌ Ошибка: item_id уже существует.")
    await state.clear()
    await admin_panel(message)

# ----- УДАЛЕНИЕ ТОВАРА -----
@router.message(DelProductStates.waiting_for_item_id)
async def delete_product_handler(message: Message, state: FSMContext):
    item_id = message.text.strip()
    success = remove_product_from_db(item_id)
    if success:
        await message.answer(f"✅ Товар с ID `{item_id}` удалён")
    else:
        await message.answer(f"❌ Товар с ID `{item_id}` не найден")
    await state.clear()
    await admin_panel(message)

# ----- ДОБАВЛЕНИЕ БАЛАНСА ПОЛЬЗОВАТЕЛЮ -----
@router.message(AddBalanceStates.waiting_for_user_id)
async def add_balance_user_id(message: Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        await state.update_data(user_id=user_id)
        await message.answer("Введите **сумму** для начисления (в рублях):")
        await state.set_state(AddBalanceStates.waiting_for_amount)
    except ValueError:
        await message.answer("❌ Введите числовой user_id")

@router.message(AddBalanceStates.waiting_for_amount)
async def add_balance_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        user_id = data['user_id']
        update_balance(user_id, amount)
        await message.answer(f"✅ Пользователю `{user_id}` начислено {amount} ₽")
        # опционально уведомить пользователя
        try:
            await message.bot.send_message(user_id, f"💰 Ваш баланс пополнен на {amount} ₽ администратором.")
        except:
            pass
    except ValueError:
        await message.answer("❌ Введите число")
    await state.clear()
    await admin_panel(message)

# ----- РАССЫЛКА -----
@router.message(lambda msg: msg.from_user.id in ADMIN_IDS and getattr(msg, 'state', None) == "waiting_for_broadcast")
async def broadcast_handler(message: Message, state: FSMContext, bot: Bot):
    users = get_all_users()
    success = 0
    fail = 0
    for user in users:
        try:
            if message.text:
                await bot.send_message(user[0], message.text)
            elif message.photo:
                await bot.send_photo(user[0], message.photo[-1].file_id, caption=message.caption)
            elif message.document:
                await bot.send_document(user[0], message.document.file_id, caption=message.caption)
            success += 1
        except:
            fail += 1
        await asyncio.sleep(0.05)
    await message.answer(f"✅ Рассылка: доставлено {success}, ошибок {fail}")
    await state.clear()
    await admin_panel(message)

# ----- КОМАНДЫ ПОДТВЕРЖДЕНИЯ / ОТМЕНЫ ЗАКАЗОВ -----
@router.message(Command("confirm"))
async def confirm_order(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    try:
        order_id = message.text.split()[1]
        order = get_order_by_id(order_id)
        if not order:
            await message.answer("❌ Заказ не найден")
            return
        update_order_status(order_id, "completed")
        await bot.send_message(order[1], f"✅ Ваш заказ #{order_id} выполнен! Спасибо.")
        await message.answer(f"✅ Заказ {order_id} подтверждён")
    except:
        await message.answer("❌ Используйте: /confirm <ID_заказа>")

@router.message(Command("decline"))
async def decline_order(message: Message, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    try:
        order_id = message.text.split()[1]
        order = get_order_by_id(order_id)
        if not order:
            await message.answer("❌ Заказ не найден")
            return
        update_order_status(order_id, "cancelled")
        await bot.send_message(order[1], f"❌ Заказ #{order_id} отменён. Средства вернутся в течение 3 дней.")
        await message.answer(f"❌ Заказ {order_id} отменён")
    except:
        await message.answer("❌ Используйте: /decline <ID_заказа>")

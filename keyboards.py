from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import load_catalog

def main_menu():
    buttons = [
        [InlineKeyboardButton(text="🛍️ Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💰 Пополнить", callback_data="deposit")],
        [InlineKeyboardButton(text="🎁 Промокод", callback_data="promocode")],
        [InlineKeyboardButton(text="📞 Поддержка", url="https://t.me/ВАШ_ЮЗЕРНЕЙМ")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_menu():
    buttons = [
        [InlineKeyboardButton(text="📜 История покупок", callback_data="history")],
        [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="deposit")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def deposit_keyboard():
    buttons = [
        [InlineKeyboardButton(text="100 ₽", callback_data="deposit_100"),
         InlineKeyboardButton(text="300 ₽", callback_data="deposit_300")],
        [InlineKeyboardButton(text="500 ₽", callback_data="deposit_500"),
         InlineKeyboardButton(text="1000 ₽", callback_data="deposit_1000")],
        [InlineKeyboardButton(text="✏️ Другая сумма", callback_data="deposit_custom")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def catalog_keyboard():
    catalog = load_catalog()
    buttons = [[InlineKeyboardButton(text=cat["name"], callback_data=f"cat_{cat_id}")] for cat_id, cat in catalog.items()]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def items_keyboard(category_id):
    catalog = load_catalog()
    buttons = []
    for item_id, item in catalog[category_id]["items"].items():
        buttons.append([InlineKeyboardButton(text=f"{item['name']} — {item['price']}₽", callback_data=f"item_{category_id}_{item_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def item_detail_keyboard(category_id, item_id, price):
    buttons = [
        [InlineKeyboardButton(text="✅ Купить", callback_data=f"buy_{category_id}_{item_id}"),
         InlineKeyboardButton(text=f"{price}₽", callback_data="ignore")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cat_{category_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_main():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")]])

def admin_main_menu():
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="📦 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="🛍 Товары", callback_data="admin_products")],
        [InlineKeyboardButton(text="💰 Добавить баланс", callback_data="admin_add_balance")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔙 Выход", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_products_menu():
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="❌ Удалить товар", callback_data="admin_del_product")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_back_button():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]])

def admin_orders_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="admin_confirm")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")]
    ])
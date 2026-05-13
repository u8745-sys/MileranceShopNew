from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import CATALOG

def main_menu():
    buttons = [
        [InlineKeyboardButton(text="🛍️ Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💰 Пополнить", callback_data="deposit")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def catalog_menu():
    buttons = [[InlineKeyboardButton(text=cat["name"], callback_data=f"cat_{cat_id}")] for cat_id, cat in CATALOG.items()]
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def items_menu(category_id):
    buttons = []
    for item_id, item in CATALOG[category_id]["items"].items():
        buttons.append([InlineKeyboardButton(text=f"{item['name']} — {item['price']}₽", callback_data=f"buy_{category_id}_{item_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_menu():
    buttons = [[InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

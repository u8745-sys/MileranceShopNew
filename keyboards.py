from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import SUPPORT_LINK

def main_menu(balance):
    buttons = [
        [InlineKeyboardButton(text="🛍️ Каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="deposit")],
        [InlineKeyboardButton(text="🎁 Промокод", callback_data="promocode")],
        [InlineKeyboardButton(text="📞 Поддержка", url=SUPPORT_LINK)]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_menu(balance):
    buttons = [
        [InlineKeyboardButton(text="📜 История покупок", callback_data="history")],
        [InlineKeyboardButton(text="💰 Пополнить", callback_data="deposit")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def deposit_menu():
    buttons = [
        [InlineKeyboardButton(text="100 ₽", callback_data="deposit_100"),
         InlineKeyboardButton(text="300 ₽", callback_data="deposit_300")],
        [InlineKeyboardButton(text="500 ₽", callback_data="deposit_500"),
         InlineKeyboardButton(text="1000 ₽", callback_data="deposit_1000")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def catalog_menu(catalog):
    buttons = []
    for cat_id, cat_data in catalog.items():
        buttons.append([InlineKeyboardButton(text=cat_data["name"], callback_data=f"cat_{cat_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def items_menu(category_id, category_data):
    buttons = []
    for item_id, item in category_data["items"].items():
        buttons.append([InlineKeyboardButton(text=f"{item['name']} — {item['price']} ₽", callback_data=f"item_{category_id}_{item_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def item_detail_menu(category_id, item_id):
    buttons = [
        [InlineKeyboardButton(text="✅ Купить", callback_data=f"buy_{category_id}_{item_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"cat_{category_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def back_to_main():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]])

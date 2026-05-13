import sqlite3
import json
import uuid
import os

DB_NAME = "shop.db"
PRODUCTS_FILE = "products.json"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER DEFAULT 0, registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("CREATE TABLE IF NOT EXISTS orders (order_id TEXT PRIMARY KEY, user_id INTEGER, items TEXT, total INTEGER, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("CREATE TABLE IF NOT EXISTS promocodes (code TEXT PRIMARY KEY, discount_type TEXT, discount_value INTEGER, uses_left INTEGER, expires_at TIMESTAMP)")
        conn.execute("CREATE TABLE IF NOT EXISTS used_promocodes (user_id INTEGER, code TEXT, used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

def add_user(user_id, username):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT OR IGNORE INTO users (user_id, username, balance) VALUES (?, ?, 0)", (user_id, username))

def get_user_balance(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row[0] if row else 0

def update_balance(user_id, amount):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))

def add_order(user_id, items, total):
    order_id = str(uuid.uuid4())[:8]
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO orders (order_id, user_id, items, total, status) VALUES (?, ?, ?, ?, 'completed')", (order_id, user_id, json.dumps(items), total))
    return order_id

def get_user_orders(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT order_id, items, total, status, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()

def add_promocode(code, discount_type, discount_value, uses_left, expires_at):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT OR REPLACE INTO promocodes VALUES (?, ?, ?, ?, ?)", (code, discount_type, discount_value, uses_left, expires_at))

def get_promocode(code):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT * FROM promocodes WHERE code = ? AND uses_left > 0 AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)", (code,)).fetchone()

def use_promocode(user_id, code):
    with sqlite3.connect(DB_NAME) as conn:
        used = conn.execute("SELECT 1 FROM used_promocodes WHERE user_id = ? AND code = ?", (user_id, code)).fetchone()
        if used:
            return False
        conn.execute("UPDATE promocodes SET uses_left = uses_left - 1 WHERE code = ?", (code,))
        conn.execute("INSERT INTO used_promocodes (user_id, code) VALUES (?, ?)", (user_id, code))
        return True

def get_user_by_order_id(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute("SELECT user_id FROM orders WHERE order_id = ?", (order_id,)).fetchone()
        return row[0] if row else None

# ----- УПРАВЛЕНИЕ ТОВАРАМИ (products.json) -----
def _load_products():
    if not os.path.exists(PRODUCTS_FILE):
        return {}
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_products(products):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

def get_all_products():
    return _load_products()

def add_product_to_db(category_id, item_id, name, price, desc):
    products = _load_products()
    if category_id not in products:
        products[category_id] = {"name": category_id, "items": {}}
    if item_id in products[category_id]["items"]:
        return False
    products[category_id]["items"][item_id] = {"name": name, "price": price, "desc": desc}
    _save_products(products)
    return True

def remove_product_from_db(item_id):
    products = _load_products()
    for cat_id, cat_data in products.items():
        if item_id in cat_data["items"]:
            del cat_data["items"][item_id]
            # если категория опустела, удаляем её
            if not cat_data["items"]:
                del products[cat_id]
            _save_products(products)
            return True
    return False

def get_all_users():
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT user_id, username, balance, registered_at FROM users ORDER BY registered_at DESC").fetchall()

def get_all_orders():
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT order_id, user_id, total, status, created_at FROM orders ORDER BY created_at DESC").fetchall()

def get_order_by_id(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()

def get_stats():
    with sqlite3.connect(DB_NAME) as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        completed_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'").fetchone()[0]
        total_amount = conn.execute("SELECT SUM(total) FROM orders WHERE status = 'completed'").fetchone()[0] or 0
        pending_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'").fetchone()[0]
        return {"users": users, "total_orders": total_orders, "completed_orders": completed_orders, "total_amount": total_amount, "pending_orders": pending_orders}

def get_pending_orders_count():
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'").fetchone()[0]

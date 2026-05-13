import sqlite3
import json
import uuid
import os

DB_NAME = "shop.db"
PRODUCTS_FILE = "products.json"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER DEFAULT 0, registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("CREATE TABLE IF NOT EXISTS deposit_orders (order_id TEXT PRIMARY KEY, user_id INTEGER, amount INTEGER, status TEXT DEFAULT 'pending', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("CREATE TABLE IF NOT EXISTS purchases (purchase_id TEXT PRIMARY KEY, user_id INTEGER, item_name TEXT, price INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
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

def add_deposit_order(user_id, amount):
    order_id = str(uuid.uuid4())[:8]
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO deposit_orders (order_id, user_id, amount, status) VALUES (?, ?, ?, 'pending')", (order_id, user_id, amount))
    return order_id

def complete_deposit_order(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute("SELECT user_id, amount FROM deposit_orders WHERE order_id = ? AND status = 'pending'", (order_id,)).fetchone()
        if row:
            user_id, amount = row
            conn.execute("UPDATE deposit_orders SET status = 'completed' WHERE order_id = ?", (order_id,))
            conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            return True
        return False

def add_purchase(user_id, item_name, price):
    purchase_id = str(uuid.uuid4())[:8]
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO purchases (purchase_id, user_id, item_name, price) VALUES (?, ?, ?, ?)", (purchase_id, user_id, item_name, price))

def get_user_purchases(user_id, limit=10):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT purchase_id, item_name, price, created_at FROM purchases WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()

def add_promocode(code, discount_type, discount_value, uses_left, expires_at=None):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT OR REPLACE INTO promocodes (code, discount_type, discount_value, uses_left, expires_at) VALUES (?, ?, ?, ?, ?)",
                     (code, discount_type, discount_value, uses_left, expires_at))

def get_promocode(code):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT code, discount_type, discount_value, uses_left, expires_at FROM promocodes WHERE code = ? AND uses_left > 0 AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)", (code,)).fetchone()

def use_promo_code(user_id, code):
    with sqlite3.connect(DB_NAME) as conn:
        used = conn.execute("SELECT 1 FROM used_promocodes WHERE user_id = ? AND code = ?", (user_id, code)).fetchone()
        if used:
            return False
        promo = conn.execute("SELECT discount_type, discount_value FROM promocodes WHERE code = ? AND uses_left > 0", (code,)).fetchone()
        if not promo:
            return False
        conn.execute("UPDATE promocodes SET uses_left = uses_left - 1 WHERE code = ?", (code,))
        conn.execute("INSERT INTO used_promocodes (user_id, code) VALUES (?, ?)", (user_id, code))
        return promo

def load_catalog():
    if not os.path.exists(PRODUCTS_FILE):
        # Инициализируем из config.CATALOG, если файла нет
        from config import CATALOG as default_catalog
        save_catalog(default_catalog)
        return default_catalog
    with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_catalog(catalog):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

def get_all_products():
    return load_catalog()

def add_product_to_db(category_id, item_id, name, price, desc):
    products = load_catalog()
    if category_id not in products:
        products[category_id] = {"name": category_id, "items": {}}
    if item_id in products[category_id]["items"]:
        return False
    products[category_id]["items"][item_id] = {"name": name, "price": price, "desc": desc}
    save_catalog(products)
    return True

def remove_product_from_db(item_id):
    products = load_catalog()
    for cat_id, cat_data in products.items():
        if item_id in cat_data["items"]:
            del cat_data["items"][item_id]
            if not cat_data["items"]:
                del products[cat_id]
            save_catalog(products)
            return True
    return False

def get_all_users():
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT user_id, username, balance, registered_at FROM users ORDER BY registered_at DESC").fetchall()

def get_all_deposit_orders():
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT order_id, user_id, amount, status, created_at FROM deposit_orders ORDER BY created_at DESC").fetchall()

def get_deposit_order_by_id(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT * FROM deposit_orders WHERE order_id = ?", (order_id,)).fetchone()

def get_stats():
    with sqlite3.connect(DB_NAME) as conn:
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_deposits = conn.execute("SELECT COUNT(*) FROM deposit_orders WHERE status='completed'").fetchone()[0]
        total_amount = conn.execute("SELECT SUM(amount) FROM deposit_orders WHERE status='completed'").fetchone()[0] or 0
        pending_deposits = conn.execute("SELECT COUNT(*) FROM deposit_orders WHERE status='pending'").fetchone()[0]
        return {"users": users, "total_orders": total_deposits, "completed_orders": total_deposits, "total_amount": total_amount, "pending_orders": pending_deposits}

def get_pending_orders_count():
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT COUNT(*) FROM deposit_orders WHERE status='pending'").fetchone()[0]

def update_order_status(order_id, status):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE deposit_orders SET status = ? WHERE order_id = ?", (status, order_id))

import sqlite3
import json
import uuid

DB_NAME = "shop.db"
PRODUCTS_FILE = "products.json"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        # Таблица пользователей
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Таблица заказов (пополнений и покупок)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                user_id INTEGER,
                amount INTEGER,
                type TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Таблица промокодов
        conn.execute("""
            CREATE TABLE IF NOT EXISTS promocodes (
                code TEXT PRIMARY KEY,
                discount INTEGER,
                uses_left INTEGER,
                expires_at TIMESTAMP
            )
        """)
        # Таблица использованных промокодов пользователями
        conn.execute("""
            CREATE TABLE IF NOT EXISTS used_promocodes (
                user_id INTEGER,
                code TEXT,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Таблица заказов на покупку товаров (история)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                purchase_id TEXT PRIMARY KEY,
                user_id INTEGER,
                item_id TEXT,
                item_name TEXT,
                price INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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

def add_deposit_order(order_id, user_id, amount):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO orders (order_id, user_id, amount, type, status) VALUES (?, ?, ?, 'deposit', 'pending')", (order_id, user_id, amount))

def complete_deposit_order(order_id):
    with sqlite3.connect(DB_NAME) as conn:
        # Получаем сумму и пользователя
        row = conn.execute("SELECT user_id, amount FROM orders WHERE order_id = ? AND type='deposit'", (order_id,)).fetchone()
        if row:
            user_id, amount = row
            conn.execute("UPDATE orders SET status = 'completed' WHERE order_id = ?", (order_id,))
            update_balance(user_id, amount)
            return True
        return False

def add_purchase(user_id, item_id, item_name, price):
    purchase_id = str(uuid.uuid4())[:8]
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO purchases (purchase_id, user_id, item_id, item_name, price) VALUES (?, ?, ?, ?, ?)", (purchase_id, user_id, item_id, item_name, price))
    return purchase_id

def get_user_purchases(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT purchase_id, item_name, price, created_at FROM purchases WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()

def add_promocode(code, discount, uses_left, expires_at):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT OR REPLACE INTO promocodes (code, discount, uses_left, expires_at) VALUES (?, ?, ?, ?)", (code, discount, uses_left, expires_at))

def get_promocode(code):
    with sqlite3.connect(DB_NAME) as conn:
        return conn.execute("SELECT discount, uses_left, expires_at FROM promocodes WHERE code = ? AND uses_left > 0 AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)", (code,)).fetchone()

def use_promocode(user_id, code):
    with sqlite3.connect(DB_NAME) as conn:
        used = conn.execute("SELECT 1 FROM used_promocodes WHERE user_id = ? AND code = ?", (user_id, code)).fetchone()
        if used:
            return False
        conn.execute("UPDATE promocodes SET uses_left = uses_left - 1 WHERE code = ?", (code,))
        conn.execute("INSERT INTO used_promocodes (user_id, code) VALUES (?, ?)", (user_id, code))
        return True

def save_catalog(catalog):
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

def load_catalog():
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

import sqlite3
import json
import uuid

DB_NAME = "shop.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, balance INTEGER DEFAULT 0)")
        conn.execute("CREATE TABLE IF NOT EXISTS orders (order_id TEXT PRIMARY KEY, user_id INTEGER, items TEXT, total INTEGER, status TEXT)")

def add_user(user_id, username):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT OR IGNORE INTO users (user_id, username, balance) VALUES (?, ?, 0)", (user_id, username))

def get_balance(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        row = conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row[0] if row else 0

def update_balance(user_id, amount):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))

def add_order(user_id, items, total):
    order_id = str(uuid.uuid4())[:8]
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO orders (order_id, user_id, items, total, status) VALUES (?, ?, ?, ?, 'paid')", (order_id, user_id, json.dumps(items), total))
    return order_id

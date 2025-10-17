# orders.py
import sqlite3
from database import DB_FILE

def create_order(user_id, service_id, details):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, service_id, details) VALUES (?, ?, ?)", (user_id, service_id, details))
    conn.commit()
    conn.close()

def get_all_orders():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = c.fetchall()
    conn.close()
    return orders

def update_order_status(order_id, new_status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
    conn.commit()
    conn.close()

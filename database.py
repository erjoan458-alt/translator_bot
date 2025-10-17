# database.py
import sqlite3

DB_FILE = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # جدول الخدمات
    c.execute('''CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    description TEXT,
                    price REAL
                )''')

    # جدول الطلبات
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    service_id INTEGER,
                    details TEXT,
                    status TEXT DEFAULT 'قيد المراجعة'
                )''')

    conn.commit()
    conn.close()

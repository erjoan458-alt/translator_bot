# services.py
import sqlite3
from database import DB_FILE

def add_service(name, description, price):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO services (name, description, price) VALUES (?, ?, ?)", (name, description, price))
    conn.commit()
    conn.close()

def edit_service(service_id, name, description, price):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE services SET name=?, description=?, price=? WHERE id=?", (name, description, price, service_id))
    conn.commit()
    conn.close()

def delete_service(service_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM services WHERE id=?", (service_id,))
    conn.commit()
    conn.close()

def get_all_services():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM services")
    services = c.fetchall()
    conn.close()
    return services

def get_service(service_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM services WHERE id=?", (service_id,))
    service = c.fetchone()
    conn.close()
    return service

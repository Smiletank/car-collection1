import sqlite3
import os
from datetime import datetime

# Streamlit Cloud 用 /tmp 目录，本地用 data 目录
if os.path.exists('/mount/src'):
    DB_PATH = "/tmp/cars.db"
    IMAGE_DIR = "/tmp/images"
else:
    DB_PATH = "data/cars.db"
    IMAGE_DIR = "data/images"

os.makedirs(IMAGE_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT,
            model TEXT,
            color TEXT,
            series TEXT,
            note TEXT,
            side_image TEXT,
            bottom_image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_car(brand, model, color, series, note, side_image, bottom_image):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cars (brand, model, color, series, note, side_image, bottom_image)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (brand, model, color, series, note, side_image, bottom_image))
    conn.commit()
    conn.close()

def get_all_cars():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cars ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def search_cars(brand=None, model=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT * FROM cars WHERE 1=1"
    params = []
    if brand:
        query += " AND brand LIKE ?"
        params.append(f"%{brand}%")
    if model:
        # 更宽松的匹配：只要包含关键词就算
        # 把车型名称拆成关键词，每个关键词都匹配
        keywords = model.replace('-', ' ').replace('_', ' ').split()
        for kw in keywords:
            if len(kw) > 2:  # 忽略太短的关键词
                query += f" AND (model LIKE ? OR ? LIKE '%' || model || '%')"
                params.extend([f"%{kw}%", kw])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_car(car_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cars WHERE id = ?', (car_id,))
    conn.commit()
    conn.close()

init_db()

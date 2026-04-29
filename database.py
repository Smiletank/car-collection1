import os
from datetime import datetime
from libsql_client import Client

# Turso 云数据库配置
DB_URL = "libsql://car-collection-smiletank.aws-ap-northeast-1.turso.io"
DB_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3Nzc0NzQzNDYsImlkIjoiMDE5ZGQ5YTktZjgwMS03ZDA3LTk0OGUtMDVmOTJjOTQwMTBkIiwicmlkIjoiZTEyMDczNjUtNGRkNC00YjRhLWFkNDktOGMwODZlMzlhMDEzIn0.uvQqqnxpUL1CL_bZiBLGfH5Jw3SQi9z-N0d7BUpEZ7Xc1SthWoEuWGKsMsfY_x7LrYFnszGqvGnFErPIzEqDCw"

# 图片存储目录
if os.path.exists('/mount/src'):
    IMAGE_DIR = "/tmp/images"
else:
    IMAGE_DIR = "data/images"
os.makedirs(IMAGE_DIR, exist_ok=True)

def get_conn():
    """获取数据库连接"""
    return Client(url=DB_URL, auth_token=DB_TOKEN)

def init_db():
    """初始化数据库"""
    conn = get_conn()
    conn.execute('''
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
    conn.close()

def add_car(brand, model, color, series, note, side_image, bottom_image):
    """添加一辆车到数据库"""
    conn = get_conn()
    conn.execute('''
        INSERT INTO cars (brand, model, color, series, note, side_image, bottom_image)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (brand, model, color, series, note, side_image, bottom_image))
    conn.close()

def get_all_cars():
    """获取所有收藏"""
    conn = get_conn()
    result = conn.execute('SELECT * FROM cars ORDER BY created_at DESC')
    rows = result.rows
    conn.close()
    return [list(row.values()) for row in rows]

def search_cars(brand=None, model=None):
    """搜索相似车型"""
    conn = get_conn()
    query = "SELECT * FROM cars WHERE 1=1"
    params = []
    if brand:
        query += " AND brand LIKE ?"
        params.append(f"%{brand}%")
    if model:
        keywords = model.replace('-', ' ').replace('_', ' ').split()
        for kw in keywords:
            if len(kw) > 2:
                query += f" AND (model LIKE ? OR ? LIKE '%' || model || '%')"
                params.extend([f"%{kw}%", kw])
    result = conn.execute(query, params)
    rows = result.rows
    conn.close()
    return [list(row.values()) for row in rows]

def delete_car(car_id):
    """删除一辆车"""
    conn = get_conn()
    conn.execute('DELETE FROM cars WHERE id = ?', (car_id,))
    conn.close()

init_db()

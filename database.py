"""
Supabase数据库操作模块
使用requests直接调Supabase REST API，避免httpx兼容问题
"""

import uuid
import requests

# Supabase配置
SUPABASE_URL = "https://cwtxyyhmusxzlprgzj.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3dHhjeXlobXVzeHpscHByZ3pqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0Nzc1NDcsImV4cCI6MjA5MzA1MzU0N30.nQkTbGUNLehC9wE6WCsUPek7G3WIzNxVuoVV0JUb33M"
STORAGE_BUCKET = "car-images"

_headers = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}


def init_supabase():
    """初始化（返回None，保持接口兼容）"""
    return None


def upload_image(supabase, file_bytes: bytes, file_name: str) -> str:
    """上传图片到Supabase Storage，返回公开URL"""
    unique_name = f"{uuid.uuid4().hex}_{file_name}"
    
    if file_name.lower().endswith('.png'):
        content_type = "image/png"
    elif file_name.lower().endswith(('.jpg', '.jpeg')):
        content_type = "image/jpeg"
    else:
        content_type = "application/octet-stream"
    
    url = f"{SUPABASE_URL}/storage/v1/object/{STORAGE_BUCKET}/{unique_name}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": content_type,
    }
    
    resp = requests.post(url, headers=headers, data=file_bytes, timeout=30)
    if resp.status_code in (200, 201):
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{unique_name}"
        return public_url
    
    # 如果文件已存在，尝试更新
    url = f"{SUPABASE_URL}/storage/v1/object/{STORAGE_BUCKET}/{unique_name}"
    resp = requests.put(url, headers=headers, data=file_bytes, timeout=30)
    if resp.status_code in (200, 201):
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{unique_name}"
        return public_url
    
    raise Exception(f"图片上传失败: {resp.status_code} {resp.text}")


def get_image_url(supabase, file_path: str) -> str:
    """获取图片公开URL"""
    return f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{file_path}"


def add_car(supabase, car_name: str, color: str, brand: str,
            side_image_url: str, bottom_image_url: str) -> dict:
    """添加车辆到数据库"""
    data = {
        "car_name": car_name,
        "color": color,
        "brand": brand,
        "side_image_url": side_image_url,
        "bottom_image_url": bottom_image_url,
    }
    
    url = f"{SUPABASE_URL}/rest/v1/cars"
    resp = requests.post(url, headers=_headers, json=data, timeout=30)
    
    if resp.status_code in (200, 201):
        result = resp.json()
        return result[0] if isinstance(result, list) else result
    
    raise Exception(f"入库失败: {resp.status_code} {resp.text}")


def get_all_cars(supabase) -> list:
    """获取所有车辆，按入库时间倒序"""
    url = f"{SUPABASE_URL}/rest/v1/cars"
    params = {"order": "created_at.desc"}
    resp = requests.get(url, headers=_headers, params=params, timeout=30)
    
    if resp.status_code == 200:
        return resp.json()
    
    raise Exception(f"获取数据失败: {resp.status_code} {resp.text}")


def search_duplicates(supabase, car_name: str) -> list:
    """
    宽松查重：把车型名称按空格和连字符拆分关键词，任一关键词匹配即算可能重复
    """
    keywords = car_name.replace('-', ' ').replace('_', ' ').split()
    keywords = [k for k in keywords if len(k) >= 2]
    
    if not keywords:
        return []
    
    # 用or条件拼接多个关键词搜索
    or_conditions = ",".join([f'car_name.ilike.*{k}*' for k in keywords])
    url = f"{SUPABASE_URL}/rest/v1/cars"
    params = {"or": f"({or_conditions})", "order": "created_at.desc"}
    resp = requests.get(url, headers=_headers, params=params, timeout=30)
    
    if resp.status_code == 200:
        return resp.json()
    
    return []


def delete_car(supabase, car_id: int) -> bool:
    """删除车辆"""
    url = f"{SUPABASE_URL}/rest/v1/cars"
    params = {"id": f"eq.{car_id}"}
    resp = requests.delete(url, headers=_headers, params=params, timeout=30)
    return resp.status_code in (200, 204)

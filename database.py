"""
Supabase数据库操作模块
负责与Supabase数据库和Storage的交互
"""

import uuid
from supabase import create_client, Client

# Supabase配置
SUPABASE_URL = "https://cwtxyyhmusxzlprgzj.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3dHhjeXlobXVzeHpscHByZ3pqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0Nzc1NDcsImV4cCI6MjA5MzA1MzU0N30.nQkTbGUNLehC9wE6WCsUPek7G3WIzNxVuoVV0JUb33M"
STORAGE_BUCKET = "car-images"


def init_supabase() -> Client:
    """初始化Supabase客户端"""
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def upload_image(supabase: Client, file_bytes: bytes, file_name: str) -> str:
    """
    上传图片到Supabase Storage，返回公开URL
    
    Args:
        supabase: Supabase客户端
        file_bytes: 图片字节数据
        file_name: 原始文件名
    
    Returns:
        公开访问URL
    """
    # 生成唯一文件名
    unique_name = f"{uuid.uuid4().hex}_{file_name}"
    
    # 确定content-type
    if file_name.lower().endswith('.png'):
        content_type = "image/png"
    elif file_name.lower().endswith(('.jpg', '.jpeg')):
        content_type = "image/jpeg"
    else:
        content_type = "application/octet-stream"
    
    try:
        response = supabase.storage.from_(STORAGE_BUCKET).upload(
            unique_name,
            file_bytes,
            {"content-type": content_type}
        )
        
        # 获取公开URL
        public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(unique_name)
        return public_url
    
    except Exception as e:
        # 如果文件已存在，尝试覆盖
        try:
            supabase.storage.from_(STORAGE_BUCKET).update(
                unique_name,
                file_bytes,
                {"content-type": content_type}
            )
            public_url = supabase.storage.from_(STORAGE_BUCKET).get_public_url(unique_name)
            return public_url
        except Exception:
            raise Exception(f"图片上传失败: {str(e)}")


def get_image_url(supabase: Client, file_name: str) -> str:
    """获取图片公开URL"""
    return supabase.storage.from_(STORAGE_BUCKET).get_public_url(file_name)


def add_car(supabase: Client, car_name: str, color: str, brand: str, 
            side_image_url: str, bottom_image_url: str) -> dict:
    """
    添加车辆到数据库
    
    Args:
        supabase: Supabase客户端
        car_name: 车型名称
        color: 颜色
        brand: 品牌
        side_image_url: 侧视图URL
        bottom_image_url: 底盘图URL
    
    Returns:
        插入的数据（含id）
    """
    data = {
        "car_name": car_name,
        "color": color,
        "brand": brand,
        "side_image_url": side_image_url,
        "bottom_image_url": bottom_image_url,
    }
    
    response = supabase.table("cars").insert(data).execute()
    return response.data[0] if response.data else None


def get_all_cars(supabase: Client) -> list:
    """获取所有车辆，按入库时间倒序"""
    response = supabase.table("cars").select("*").order("created_at", desc=True).execute()
    return response.data


def search_duplicates(supabase: Client, car_name: str) -> list:
    """
    宽松查重：把车型名称按空格和连字符拆分关键词，任一关键词匹配即算可能重复
    
    Args:
        supabase: Supabase客户端
        car_name: 车型名称关键词
    
    Returns:
        可能的重复车辆列表
    """
    # 清理输入并拆分关键词
    keywords = car_name.replace('-', ' ').replace('_', ' ').split()
    keywords = [k.strip().lower() for k in keywords if k.strip()]
    
    if not keywords:
        return []
    
    # 获取所有车辆进行匹配
    all_cars = get_all_cars(supabase)
    duplicates = []
    
    for car in all_cars:
        stored_name = car.get("car_name", "").lower()
        # 检查任一关键词是否匹配
        for keyword in keywords:
            if keyword and len(keyword) >= 2:  # 至少2个字符
                if keyword in stored_name:
                    duplicates.append(car)
                    break
    
    return duplicates


def check_duplicate_by_name(supabase: Client, car_name: str) -> list:
    """检查是否有重复车型"""
    return search_duplicates(supabase, car_name)

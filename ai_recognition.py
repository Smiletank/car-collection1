import base64
from zhipuai import ZhipuAI
import json
import re

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def parse_json(text):
    """更健壮的JSON解析"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except:
        pass
    
    # 尝试提取JSON块
    json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    
    # 尝试修复常见问题
    text = text.replace("'", '"')  # 单引号改双引号
    text = re.sub(r',\s*}', '}', text)  # 移除多余的逗号
    text = re.sub(r',\s*]', ']', text)
    
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    
    return {}

def recognize_bottom(image_path, api_key):
    """
    识别底盘图片，提取车辆信息
    返回：{"brand": "", "model": "", "series": ""}
    """
    client = ZhipuAI(api_key=api_key)
    image_base64 = encode_image(image_path)
    
    prompt = """
请识别这张玩具车底盘图片中的文字信息，返回JSON格式：
{"brand": "品牌", "model": "车型名称", "series": "系列"}

品牌填：风火轮、火柴盒、TLV、多美卡等
车型名称：底盘上的具体车名
系列：如果有写系列名称就填，没有就留空
"""

    response = client.chat.completions.create(
        model="glm-4v-flash",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        ],
    )
    
    result_text = response.choices[0].message.content
    result = parse_json(result_text)
    
    return {
        "brand": result.get("brand", ""),
        "model": result.get("model", ""),
        "series": result.get("series", "")
    }


def recognize_side(image_path, api_key):
    """
    识别侧视图图片，提取颜色信息
    返回：{"color": ""}
    """
    client = ZhipuAI(api_key=api_key)
    image_base64 = encode_image(image_path)
    
    prompt = """
请看这张玩具车侧视图图片，告诉我这辆车的主要颜色。

直接返回JSON格式：
{"color": "颜色描述"}

颜色用简洁的中文描述，比如：深蓝色、红色、金色、黑黄配色等。
"""

    response = client.chat.completions.create(
        model="glm-4v-flash",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        ],
    )
    
    result_text = response.choices[0].message.content
    result = parse_json(result_text)
    
    return {"color": result.get("color", "")}


def recognize_both(side_path, bottom_path, api_key):
    """
    同时识别侧视图和底盘图，返回完整信息
    """
    side_result = recognize_side(side_path, api_key)
    bottom_result = recognize_bottom(bottom_path, api_key)
    
    return {
        "brand": bottom_result.get("brand", ""),
        "model": bottom_result.get("model", ""),
        "series": bottom_result.get("series", ""),
        "color": side_result.get("color", "")
    }


def recognize_cars(image_path, api_key):
    """
    识别图片中的小车（用于查重）
    返回列表
    """
    client = ZhipuAI(api_key=api_key)
    image_base64 = encode_image(image_path)
    
    prompt = """
请识别图片中的所有玩具车，返回JSON数组：
[{"brand": "品牌", "model": "车型", "color": "颜色"}]
"""

    response = client.chat.completions.create(
        model="glm-4v-flash",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        ],
    )
    
    result_text = response.choices[0].message.content
    
    # 尝试解析数组
    json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except:
            pass
    
    return []

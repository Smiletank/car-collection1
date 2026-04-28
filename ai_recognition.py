import base64
from zhipuai import ZhipuAI
import json
import re

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def recognize_bottom(image_path, api_key):
    """
    识别底盘图片，提取车辆信息
    返回：{"brand": "", "model": "", "series": ""}
    """
    client = ZhipuAI(api_key=api_key)
    image_base64 = encode_image(image_path)
    
    prompt = """
你是风火轮/火柴盒玩具车收藏专家。请仔细识别这张底盘图片中的所有文字信息。

请提取：
- brand: 品牌（风火轮/Hot Wheels、火柴盒/Matchbox、TLV、多美卡/Tomica等）
- model: 具体车型名称（如：Ford F150 Lightning、Nissan Skyline R32等）
- series: 系列名称（如：Super Truck、Mainline、Car Culture等）

请以JSON格式返回：
{"brand": "品牌", "model": "车型名称", "series": "系列"}

如果某个字段无法识别，请返回空字符串。
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
    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
    
    if json_match:
        return json.loads(json_match.group())
    return {"brand": "", "model": "", "series": ""}


def recognize_side(image_path, api_key):
    """
    识别侧视图图片，提取颜色信息
    返回：{"color": ""}
    """
    client = ZhipuAI(api_key=api_key)
    image_base64 = encode_image(image_path)
    
    prompt = """
你是一个玩具车收藏专家。请识别这张玩具车侧视图图片，告诉我这辆车的主要颜色。

只需要返回一个颜色描述，比如：深蓝色、红色、金色、黑黄配色等。
如果车身有多种颜色，用"配色"描述，如：黑白配色、蓝红配色。

请以JSON格式返回：
{"color": "颜色描述"}
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
    json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
    
    if json_match:
        return json.loads(json_match.group())
    return {"color": ""}


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
你是1:64合金小车收藏专家。请识别图片中的所有小车模型。

对于每辆车，请识别：
- brand: 品牌（风火轮、火柴盒、TLV、多美卡、其他）
- model: 车型名称（尽量具体）
- color: 颜色

返回JSON数组：
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
    json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
    
    if json_match:
        return json.loads(json_match.group())
    return []

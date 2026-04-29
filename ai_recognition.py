"""
AI图像识别模块
使用智谱GLM-4V-flash识别车辆信息
"""

import json
import base64
import re
import requests


ZHIPU_API_ENDPOINT = "https://open.bigmodel.cn/api/paas/v4/chat/completions"


def encode_image_to_base64(image_bytes: bytes) -> str:
    """将图片字节转换为base64字符串"""
    return base64.b64encode(image_bytes).decode("utf-8")


def extract_json_from_response(text: str) -> dict:
    """
    健壮地从AI响应中提取JSON
    处理各种格式不规范的情况
    """
    text = text.strip()
    
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 尝试从代码块中提取
    code_block_patterns = [
        r'```json\s*([\s\S]*?)\s*```',
        r'```\s*([\s\S]*?)\s*```',
    ]
    
    for pattern in code_block_patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                continue
    
    # 尝试找到JSON对象的开始和结束
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        json_str = text[start_idx:end_idx + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # 尝试修复常见问题
    # 1. 移除尾部的逗号
    fixed = re.sub(r',\s*([}\]])', r'\1', text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    
    # 2. 修复单引号为双引号
    fixed = re.sub(r"'([^']*)':", r'"\1":', text)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    
    raise ValueError(f"无法解析AI响应: {text[:200]}")


def recognize_car_from_bottom(image_bytes: bytes, api_key: str) -> str:
    """
    从底盘图识别车型名称
    
    Args:
        image_bytes: 底盘图字节数据
        api_key: 智谱API Key
    
    Returns:
        识别的车型名称
    """
    base64_image = encode_image_to_base64(image_bytes)
    
    prompt = """你是一个专业的汽车识别专家。请仔细分析这张底盘/底部图片，识别出这辆车的具体车型名称。

请只返回JSON格式的识别结果，不要包含任何其他文字：
```json
{
    "car_name": "识别出的车型名称，例如：Ford F-150 Lightning"
}
```

注意事项：
1. 如果无法确定具体车型，请给出最可能的猜测
2. 车型名称应包含品牌和具体车型
3. 如果图片质量太差无法识别，返回空的car_name"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "glm-4v-flash",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            ZHIPU_API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # 解析JSON响应
        parsed = extract_json_from_response(content)
        car_name = parsed.get("car_name", "").strip()
        
        return car_name if car_name else "未能识别车型"
    
    except requests.exceptions.Timeout:
        raise Exception("AI识别超时，请重试")
    except requests.exceptions.RequestException as e:
        raise Exception(f"API请求失败: {str(e)}")
    except Exception as e:
        raise Exception(f"车型识别失败: {str(e)}")


def recognize_color_from_side(image_bytes: bytes, api_key: str) -> str:
    """
    从侧视图识别车辆颜色
    
    Args:
        image_bytes: 侧视图字节数据
        api_key: 智谱API Key
    
    Returns:
        识别的车辆颜色
    """
    base64_image = encode_image_to_base64(image_bytes)
    
    prompt = """你是一个专业的汽车颜色识别专家。请仔细分析这张汽车侧视图，识别出这辆车的准确颜色。

请只返回JSON格式的识别结果，不要包含任何其他文字：
```json
{
    "color": "识别出的颜色，例如：火焰红、珍珠白、深空灰、午夜蓝"
}
```

注意事项：
1. 请给出准确的中文颜色描述
2. 如果是金属漆或珍珠漆，请加上相应描述（如"珍珠白"、"金属灰"）
3. 如果是双色车身，请以主要颜色为准
4. 如果无法确定，返回"未知颜色" """
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "glm-4v-flash",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(
            ZHIPU_API_ENDPOINT,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # 解析JSON响应
        parsed = extract_json_from_response(content)
        color = parsed.get("color", "").strip()
        
        return color if color else "未知颜色"
    
    except requests.exceptions.Timeout:
        raise Exception("AI识别超时，请重试")
    except requests.exceptions.RequestException as e:
        raise Exception(f"API请求失败: {str(e)}")
    except Exception as e:
        raise Exception(f"颜色识别失败: {str(e)}")

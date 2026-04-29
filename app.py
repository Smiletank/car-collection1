"""
小车收藏管理应用
基于Streamlit + Supabase 构建
"""

import streamlit as st
from datetime import datetime
from database import (
    init_supabase, add_car, get_all_cars, 
    search_duplicates, upload_image
)
from ai_recognition import recognize_car_from_bottom, recognize_color_from_side


# 页面配置
st.set_page_config(
    page_title="🚗 小车收藏管理",
    page_icon="🚗",
    layout="wide"
)


def init_session_state():
    """初始化session state"""
    if "zhipu_api_key" not in st.session_state:
        st.session_state.zhipu_api_key = ""
    if "recognized_data" not in st.session_state:
        st.session_state.recognized_data = None
    if "supabase_client" not in st.session_state:
        st.session_state.supabase_client = None


def get_supabase_client():
    """获取或初始化Supabase客户端"""
    if st.session_state.supabase_client is None:
        try:
            st.session_state.supabase_client = init_supabase()
        except Exception as e:
            st.error(f"数据库连接失败: {str(e)}")
            return None
    # init_supabase返回None是正常的（改用requests直连），不阻断流程
    return st.session_state.supabase_client


def render_sidebar():
    """渲染侧边栏配置"""
    with st.sidebar:
        st.title("⚙️ 配置")
        st.divider()
        
        # API Key输入
        st.session_state.zhipu_api_key = st.text_input(
            "🔑 智谱API Key",
            value=st.session_state.zhipu_api_key,
            type="password",
            help="用于AI图像识别，需要智谱AI的API Key"
        )
        
        if not st.session_state.zhipu_api_key:
            st.warning("⚠️ 请先输入智谱API Key以启用AI识别功能")
        
        st.divider()
        st.caption("🚗 小车收藏管理 v1.0")


def render_add_car_page(supabase):
    """渲染录入车辆页面"""
    st.header("📝 录入新车辆")
    
    # 检查API Key
    if not st.session_state.zhipu_api_key:
        st.error("请先在侧边栏输入智谱API Key")
        return
    
    # 文件上传区域
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📷 侧视图")
        side_file = st.file_uploader(
            "上传车辆侧视图",
            type=["jpg", "jpeg", "png"],
            help="从侧面拍摄的照片，用于识别颜色"
        )
        if side_file:
            st.image(side_file, width=300)
    
    with col2:
        st.subheader("🔧 底盘图")
        bottom_file = st.file_uploader(
            "上传底盘图",
            type=["jpg", "jpeg", "png"],
            help="从底部拍摄的照片，用于识别车型"
        )
        if bottom_file:
            st.image(bottom_file, width=300)
    
    st.divider()
    
    # AI识别按钮
    if st.button("🤖 AI识别", type="primary", use_container_width=True):
        if not side_file or not bottom_file:
            st.error("请先上传两张图片")
        else:
            with st.spinner("正在识别车型..."):
                try:
                    # 读取文件字节
                    side_bytes = side_file.getvalue()
                    bottom_bytes = bottom_file.getvalue()
                    
                    # 识别底盘图获取车型
                    car_name = recognize_car_from_bottom(bottom_bytes, st.session_state.zhipu_api_key)
                    
                    # 识别侧视图获取颜色
                    color = recognize_color_from_side(side_bytes, st.session_state.zhipu_api_key)
                    
                    # 提取品牌（简化处理）
                    brand = car_name.split()[0] if car_name and "未能" not in car_name else ""
                    
                    # 保存识别结果
                    st.session_state.recognized_data = {
                        "car_name": car_name,
                        "color": color,
                        "brand": brand,
                        "side_bytes": side_bytes,
                        "side_name": side_file.name,
                        "bottom_bytes": bottom_bytes,
                        "bottom_name": bottom_file.name
                    }
                    
                    st.success("识别完成！")
                    
                except Exception as e:
                    st.error(f"识别失败: {str(e)}")
    
    # 显示识别结果
    if st.session_state.recognized_data:
        data = st.session_state.recognized_data
        
        st.subheader("📋 识别结果")
        
        col1, col2 = st.columns(2)
        with col1:
            car_name = st.text_input("车型名称", value=data["car_name"])
        with col2:
            color = st.text_input("颜色", value=data["color"])
        
        brand = st.text_input("品牌", value=data["brand"])
        
        st.divider()
        
        # 查重检查
        duplicates = []
        if car_name and "未能" not in car_name:
            with st.spinner("正在检查重复..."):
                duplicates = search_duplicates(supabase, car_name)
        
        # 显示重复警告
        if duplicates:
            st.warning(f"⚠️ 发现 {len(duplicates)} 个可能的重复车型：")
            
            # 并排显示侧视图对比
            cols = st.columns(min(len(duplicates) + 1, 3))
            
            # 新车上传的图片
            with cols[0]:
                st.caption("📤 新车上传")
                if data.get("side_bytes"):
                    st.image(data["side_bytes"], width=200)
            
            # 已有的重复车辆
            for i, dup in enumerate(duplicates[:2]):
                with cols[i + 1]:
                    st.caption(f"📁 已存在 #{dup.get('id', i+1)}")
                    if dup.get("side_image_url"):
                        st.image(dup["side_image_url"], width=200)
                    st.caption(f"车型: {dup.get('car_name', 'N/A')}")
                    st.caption(f"颜色: {dup.get('color', 'N/A')}")
            
            if len(duplicates) > 2:
                st.info(f"还有 {len(duplicates) - 2} 个重复...")
        
        st.divider()
        
        # 入库按钮
        if st.button("✅ 确认入库", type="primary", use_container_width=True):
            if not car_name or "未能" in car_name:
                st.error("请输入有效的车型名称")
                return
            
            try:
                with st.spinner("正在上传图片..."):
                    # 上传侧视图
                    side_url = upload_image(
                        supabase, 
                        data["side_bytes"], 
                        data["side_name"]
                    )
                    
                    # 上传底盘图
                    bottom_url = upload_image(
                        supabase, 
                        data["bottom_bytes"], 
                        data["bottom_name"]
                    )
                
                with st.spinner("正在保存数据..."):
                    # 保存到数据库
                    result = add_car(
                        supabase,
                        car_name=car_name,
                        color=color or "未知",
                        brand=brand or "未知",
                        side_image_url=side_url,
                        bottom_image_url=bottom_url
                    )
                
                if result:
                    st.success(f"🎉 入库成功！车型ID: {result.get('id')}")
                    # 清空识别结果
                    st.session_state.recognized_data = None
                    st.rerun()
                else:
                    st.error("入库失败，请重试")
                    
            except Exception as e:
                st.error(f"入库失败: {str(e)}")


def render_duplicate_check_page(supabase):
    """渲染查重页面"""
    st.header("🔍 查重搜索")
    
    search_query = st.text_input(
        "输入车型名称关键词",
        placeholder="例如: F-150, Model 3, Golf R...",
        help="支持模糊匹配，输入关键词即可搜索"
    )
    
    if st.button("🔎 搜索", use_container_width=True):
        if not search_query:
            st.warning("请输入搜索关键词")
            return
        
        with st.spinner("正在搜索..."):
            duplicates = search_duplicates(supabase, search_query)
        
        if duplicates:
            st.success(f"找到 {len(duplicates)} 个匹配结果：")
            
            # 并排显示
            cols = st.columns(min(len(duplicates), 3))
            
            for i, car in enumerate(duplicates):
                with cols[i % 3]:
                    with st.container():
                        if car.get("side_image_url"):
                            st.image(car["side_image_url"], width=250)
                        else:
                            st.image("https://placehold.co/250x150?text=No+Image", width=250)
                        
                        st.markdown(f"**{car.get('car_name', 'N/A')}**")
                        st.caption(f"🎨 颜色: {car.get('color', 'N/A')}")
                        st.caption(f"🏷️ 品牌: {car.get('brand', 'N/A')}")
                        st.caption(f"🆔 ID: {car.get('id', 'N/A')}")
                        
                        # 格式化时间
                        created_at = car.get("created_at", "")
                        if created_at:
                            try:
                                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                                st.caption(f"📅 入库: {dt.strftime('%Y-%m-%d')}")
                            except:
                                pass
                        
                        st.divider()
        else:
            st.info("未找到匹配的车型")


def render_browse_page(supabase):
    """渲染收藏浏览页面"""
    st.header("🚗 我的收藏")
    
    with st.spinner("加载中..."):
        cars = get_all_cars(supabase)
    
    if not cars:
        st.info("📭 还没有收藏任何车辆，快去录入吧！")
        return
    
    st.success(f"共 {len(cars)} 辆收藏")
    st.divider()
    
    # 网格展示
    cols = st.columns(3)
    
    for i, car in enumerate(cars):
        with cols[i % 3]:
            with st.container():
                # 侧视图
                if car.get("side_image_url"):
                    st.image(car["side_image_url"], width=280)
                else:
                    st.image("https://placehold.co/280x180?text=No+Image", width=280)
                
                st.markdown(f"### {car.get('car_name', 'N/A')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.caption(f"🎨 {car.get('color', 'N/A')}")
                with col2:
                    st.caption(f"🏷️ {car.get('brand', 'N/A')}")
                
                # 时间
                created_at = car.get("created_at", "")
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        st.caption(f"📅 {dt.strftime('%Y-%m-%d %H:%M')}")
                    except:
                        st.caption(f"📅 {created_at[:10]}")
                
                st.caption(f"🆔 ID: {car.get('id', 'N/A')}")
                
                st.divider()


def main():
    """主函数"""
    init_session_state()
    render_sidebar()
    
    # 初始化Supabase客户端
    supabase = get_supabase_client()
    
    # 主内容区 - Tabs
    tab1, tab2, tab3 = st.tabs([
        "📝 录入车辆",
        "🔍 查重搜索",
        "🚗 收藏浏览"
    ])
    
    with tab1:
        render_add_car_page(supabase)
    
    with tab2:
        render_duplicate_check_page(supabase)
    
    with tab3:
        render_browse_page(supabase)


if __name__ == "__main__":
    main()

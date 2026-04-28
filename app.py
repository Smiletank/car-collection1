import streamlit as st
import os
from datetime import datetime
from PIL import Image
import pandas as pd
import database as db
import ai_recognition as ai

st.set_page_config(page_title="小车收藏管理", page_icon="🚗", layout="wide")

# 初始化session state
if 'recognition_result' not in st.session_state:
    st.session_state.recognition_result = None
if 'side_image_path' not in st.session_state:
    st.session_state.side_image_path = None
if 'bottom_image_path' not in st.session_state:
    st.session_state.bottom_image_path = None

# API Key 保存到浏览器
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

with st.sidebar:
    st.header("⚙️ 配置")
    api_key = st.text_input("智谱API Key", type="password", value=st.session_state.api_key, help="保存后会记住")
    if st.button("💾 保存API Key"):
        st.session_state.api_key = api_key
        st.success("已保存！")
    
    auto_recognize = st.checkbox("入库时自动识别底盘", value=True, help="自动识别底盘信息")
    
    st.divider()
    st.header("📊 统计")
    all_cars = db.get_all_cars()
    st.metric("总收藏", len(all_cars))
    if all_cars:
        df = pd.DataFrame(all_cars, columns=['ID', '品牌', '车型', '颜色', '系列', '编号', '备注', '侧视图', '底盘图', '入库时间'])
        st.write("品牌分布：")
        st.bar_chart(df['品牌'].value_counts())

st.title("🚗 小车收藏管理")
st.write("侧视图+底盘图录入，信息准确，查重无忧")

tab1, tab2, tab3 = st.tabs(["📸 入库", "🔍 查重", "📚 收藏库"])

# ============ 入库 ============
with tab1:
    st.header("上传车辆照片")
    st.write("需要上传两张图片：侧视图（看颜色）+ 底盘图（看信息）")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📷 侧视图")
        side_file = st.file_uploader("上传侧视图", type=['jpg', 'jpeg', 'png'], key="side_uploader")
        if side_file:
            os.makedirs(db.IMAGE_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            side_path = f"{db.IMAGE_DIR}/{timestamp}_side_{side_file.name}"
            with open(side_path, "wb") as f:
                f.write(side_file.getbuffer())
            st.session_state.side_image_path = side_path
            st.image(side_path, caption="侧视图", use_container_width=True)
    
    with col2:
        st.subheader("📷 底盘图")
        bottom_file = st.file_uploader("上传底盘图", type=['jpg', 'jpeg', 'png'], key="bottom_uploader")
        if bottom_file:
            os.makedirs(db.IMAGE_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            bottom_path = f"{db.IMAGE_DIR}/{timestamp}_bottom_{bottom_file.name}"
            with open(bottom_path, "wb") as f:
                f.write(bottom_file.getbuffer())
            st.session_state.bottom_image_path = bottom_path
            st.image(bottom_path, caption="底盘图", use_container_width=True)
    
    # 自动识别底盘信息
    if st.session_state.bottom_image_path and auto_recognize:
        st.divider()
        if st.button("🔍 识别底盘信息", type="primary"):
            if not api_key:
                st.error("请先输入智谱API Key")
            else:
                with st.spinner("识别中..."):
                    try:
                        result = ai.recognize_bottom(st.session_state.bottom_image_path, api_key)
                        st.session_state.recognition_result = result
                        st.success("识别完成！")
                    except Exception as e:
                        st.error(f"识别失败：{str(e)}")
    
    # 手动输入/编辑信息
    if st.session_state.side_image_path and st.session_state.bottom_image_path:
        st.divider()
        st.header("📝 车辆信息")
        
        # 如果有识别结果，预填充
        default_data = st.session_state.recognition_result or {}
        
        col1, col2 = st.columns(2)
        with col1:
            brand = st.text_input("品牌", value=default_data.get('brand', '风火轮'), placeholder="如：风火轮、火柴盒、TLV")
            model = st.text_input("车型名称", value=default_data.get('model', ''), placeholder="如：Ford F150 Lightning")
            color = st.text_input("颜色", value=default_data.get('color', ''), placeholder="如：深蓝色")
        
        with col2:
            series = st.text_input("系列", value=default_data.get('series', ''), placeholder="如：Super Truck")
            code = st.text_input("编号", value=default_data.get('code', ''), placeholder="如：1186, JJHE2")
            note = st.text_input("备注", value="", placeholder="其他信息")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("✅ 确认入库", type="primary"):
                if not brand or not model:
                    st.error("品牌和车型为必填项")
                else:
                    db.add_car(brand, model, color, series, code, note, 
                              st.session_state.side_image_path, st.session_state.bottom_image_path)
                    st.success("入库成功！")
                    # 清空状态
                    st.session_state.recognition_result = None
                    st.session_state.side_image_path = None
                    st.session_state.bottom_image_path = None
                    st.rerun()
        
        with col2:
            if st.button("❌ 取消"):
                st.session_state.recognition_result = None
                st.session_state.side_image_path = None
                st.session_state.bottom_image_path = None
                st.rerun()

# ============ 查重 ============
with tab2:
    st.header("🔍 查重检测")
    st.write("上传照片，检查是否已有相同车型")
    
    check_file = st.file_uploader("上传要检查的照片", type=['jpg', 'jpeg', 'png'], key="check_uploader")
    
    if check_file:
        os.makedirs(db.IMAGE_DIR, exist_ok=True)
        temp_path = f"{db.IMAGE_DIR}/temp_{check_file.name}"
        with open(temp_path, "wb") as f:
            f.write(check_file.getbuffer())
        st.image(temp_path, caption="要检查的图片", use_container_width=True)
        
        if st.button("🔍 开始查重", type="primary"):
            if not api_key:
                st.error("请先输入智谱API Key")
            else:
                with st.spinner("识别并查重中..."):
                    try:
                        result = ai.recognize_cars(temp_path, api_key)
                        st.subheader("识别结果：")
                        for i, car in enumerate(result, 1):
                            st.write(f"**第{i}辆：** {car['brand']} - {car['model']} ({car['color']})")
                            similar = db.search_cars(model=car.get('model', ''))
                            if similar:
                                st.warning(f"⚠️ 已有 {len(similar)} 辆相似车型：")
                                for s in similar:
                                    cid, brand, model, color, series, code, note, side_img, bottom_img, created_at = s[:10]
                                    col1, col2, col3 = st.columns([2, 1, 1])
                                    with col1:
                                        st.write(f"**{brand} - {model}**")
                                        st.write(f"颜色：{color} | 系列：{series} | 编号：{code}")
                                        st.write(f"入库：{created_at}")
                                    with col2:
                                        if side_img and os.path.exists(side_img):
                                            st.image(side_img, caption="侧视图", width=120)
                                    with col3:
                                        if bottom_img and os.path.exists(bottom_img):
                                            st.image(bottom_img, caption="底盘图", width=120)
                                    st.write("---")
                            else:
                                st.success("✅ 没有相似车型，可以购买！")
                            st.divider()
                    except Exception as e:
                        st.error(f"识别失败：{str(e)}")
        
        if os.path.exists(temp_path):
            os.remove(temp_path)

# ============ 收藏库 ============
with tab3:
    st.header("📚 我的收藏库")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_model = st.text_input("搜索车型")
    with col2:
        filter_brand = st.selectbox("筛选品牌", ["全部", "风火轮", "火柴盒", "TLV", "多美卡", "其他"])
    
    all_cars = db.get_all_cars()
    if all_cars:
        df = pd.DataFrame(all_cars, columns=['ID', '品牌', '车型', '颜色', '系列', '编号', '备注', '侧视图', '底盘图', '入库时间'])
        
        if search_model:
            df = df[df['车型'].str.contains(search_model, case=False, na=False)]
        if filter_brand != "全部":
            df = df[df['品牌'].str.contains(filter_brand, case=False, na=False)]
        
        st.subheader(f"共 {len(df)} 辆收藏")
        
        # 卡片展示
        for idx, row in df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    if row['侧视图'] and os.path.exists(row['侧视图']):
                        st.image(row['侧视图'], caption="侧视图", width=150)
                with col2:
                    if row['底盘图'] and os.path.exists(row['底盘图']):
                        st.image(row['底盘图'], caption="底盘图", width=150)
                with col3:
                    st.write(f"**{row['品牌']} - {row['车型']}**")
                    st.write(f"颜色：{row['颜色']} | 系列：{row['系列']}")
                    st.write(f"编号：{row['编号']}")
                    if row['备注']:
                        st.write(f"备注：{row['备注']}")
                    st.caption(f"入库：{row['入库时间']}")
                st.divider()
        
        # 删除功能
        with st.expander("🗑️ 删除收藏"):
            car_to_delete = st.selectbox(
                "选择要删除的", 
                options=df['ID'].tolist(), 
                format_func=lambda x: f"{df[df['ID']==x]['车型'].values[0]} ({df[df['ID']==x]['颜色'].values[0]})"
            )
            if st.button("删除"):
                db.delete_car(car_to_delete)
                st.success("删除成功！")
                st.rerun()
    else:
        st.info("收藏库是空的，快去入库吧！🚗")

st.divider()
st.caption("💡 保存API Key → 上传侧视图+底盘图 → 填写信息 → 入库")

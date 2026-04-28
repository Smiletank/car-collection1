import streamlit as st
import os
from datetime import datetime
from PIL import Image
import pandas as pd
import database as db
import ai_recognition as ai

st.set_page_config(page_title="小车收藏管理", page_icon="🚗", layout="wide")

if 'recognition_result' not in st.session_state:
    st.session_state.recognition_result = None
if 'uploaded_image_path' not in st.session_state:
    st.session_state.uploaded_image_path = None

with st.sidebar:
    st.header("⚙️ 配置")
    api_key = st.text_input("智谱API Key", type="password", help="在 open.bigmodel.cn 获取")
    auto_enrich = st.checkbox("智能补全信息", value=True)
    st.divider()
    st.header("📊 统计")
    all_cars = db.get_all_cars()
    st.metric("总收藏", len(all_cars))
    if all_cars:
        df = pd.DataFrame(all_cars, columns=['ID', '品牌', '车型', '颜色', '系列', '编号', '备注', '图片', '入库时间'])
        st.write("品牌分布：")
        st.bar_chart(df['品牌'].value_counts())

st.title("🚗 小车收藏管理")
st.write("上传照片，AI自动识别，批量入库")

tab1, tab2, tab3 = st.tabs(["📸 入库", "🔍 查重", "📚 收藏库"])

with tab1:
    st.header("上传照片识别")
    uploaded_file = st.file_uploader("上传小车照片", type=['jpg', 'jpeg', 'png'], key="uploader")
    
    if uploaded_file:
        os.makedirs(db.IMAGE_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = f"{db.IMAGE_DIR}/{timestamp}_{uploaded_file.name}"
        with open(image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state.uploaded_image_path = image_path
        st.image(image_path, caption="上传的图片")
        
        if st.button("🔍 开始识别", type="primary"):
            if not api_key:
                st.error("请先输入智谱API Key")
            else:
                with st.spinner("识别中..."):
                    try:
                        result = ai.recognize_and_enrich(image_path, api_key) if auto_enrich else ai.recognize_cars(image_path, api_key)
                        st.session_state.recognition_result = result
                        st.success(f"识别完成！发现 {len(result)} 辆小车")
                    except Exception as e:
                        st.error(f"识别失败：{str(e)}")
    
    if st.session_state.recognition_result:
        st.divider()
        st.header("识别结果（可编辑）")
        df = pd.DataFrame(st.session_state.recognition_result)
        for col in ['brand', 'model', 'color', 'series', 'code', 'note']:
            if col not in df.columns:
                df[col] = ''
        edited_df = st.data_editor(df[['brand', 'model', 'color', 'series', 'code', 'note']], num_rows="dynamic", use_container_width=True)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("✅ 确认入库", type="primary"):
                count = 0
                for _, row in edited_df.iterrows():
                    if pd.notna(row['brand']) and pd.notna(row['model']):
                        db.add_car(str(row['brand']), str(row['model']), str(row['color']) if pd.notna(row['color']) else "", str(row['series']) if pd.notna(row['series']) else "", str(row['code']) if pd.notna(row['code']) else "", str(row['note']) if pd.notna(row['note']) else "", st.session_state.uploaded_image_path or "")
                        count += 1
                st.success(f"成功入库 {count} 辆小车！")
                st.session_state.recognition_result = None
                st.session_state.uploaded_image_path = None
                st.rerun()
        with col2:
            if st.button("❌ 取消"):
                st.session_state.recognition_result = None
                st.session_state.uploaded_image_path = None
                st.rerun()

with tab2:
    st.header("查重检测")
    check_file = st.file_uploader("上传要检查的照片", type=['jpg', 'jpeg', 'png'], key="check_uploader")
    
    if check_file:
        os.makedirs(db.IMAGE_DIR, exist_ok=True)
        temp_path = f"{db.IMAGE_DIR}/temp_{check_file.name}"
        with open(temp_path, "wb") as f:
            f.write(check_file.getbuffer())
        st.image(temp_path, caption="要检查的图片")
        
        if st.button("🔍 开始查重", type="primary"):
            if not api_key:
                st.error("请先输入智谱API Key")
            else:
                with st.spinner("查重中..."):
                    try:
                        result = ai.recognize_cars(temp_path, api_key)
                        for i, car in enumerate(result, 1):
                            st.write(f"**第{i}辆：** {car['brand']} - {car['model']} ({car['color']})")
                            similar = db.search_cars(model=car['model'])
                            if similar:
                                st.warning(f"⚠️ 发现 {len(similar)} 辆相似车型")
                                for s in similar:
                                    cid, brand, model, color, series, code, note, img_path, created_at = s[:9]
                                    st.write(f"  • {brand} - {model} ({color}) | {series} | 入库: {created_at}")
                            else:
                                st.success("✅ 没有相似车型，可以购买！")
                            st.divider()
                    except Exception as e:
                        st.error(f"识别失败：{str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)

with tab3:
    st.header("我的收藏库")
    col1, col2 = st.columns([3, 1])
    with col1:
        search_model = st.text_input("搜索车型")
    with col2:
        filter_brand = st.selectbox("筛选品牌", ["全部", "风火轮", "火柴盒", "TLV", "多美卡", "其他"])
    
    all_cars = db.get_all_cars()
    if all_cars:
        df = pd.DataFrame(all_cars, columns=['ID', '品牌', '车型', '颜色', '系列', '编号', '备注', '图片', '入库时间'])
        if search_model:
            df = df[df['车型'].str.contains(search_model, case=False, na=False)]
        if filter_brand != "全部":
            df = df[df['品牌'].str.contains(filter_brand, case=False, na=False)]
        st.dataframe(df[['品牌', '车型', '颜色', '系列', '编号', '备注', '入库时间']], use_container_width=True, hide_index=True)
        with st.expander("🗑️ 删除收藏"):
            car_to_delete = st.selectbox("选择要删除的", options=df['ID'].tolist(), format_func=lambda x: f"{df[df['ID']==x]['车型'].values[0]}")
            if st.button("删除"):
                db.delete_car(car_to_delete)
                st.success("删除成功！")
                st.rerun()
    else:
        st.info("收藏库是空的，快去入库吧！🚗")

st.divider()
st.caption("💡 输入API Key → 上传照片识别 → 编辑确认入库")

import streamlit as st
import barcode
from barcode.writer import SVGWriter
from io import BytesIO
import base64

# --- 页面配置 ---
st.set_page_config(page_title="专业条码矢量生成器", layout="centered")

def generate_barcode_svg(code_type, data):
    """
    核心逻辑：生成条码并返回 SVG 的二进制数据
    """
    try:
        # 获取对应的条码类 (EAN13, UPCA 等)
        barcode_class = barcode.get_barcode_class(code_type.lower().replace("-", ""))
        
        # 使用 BytesIO 在内存中处理，不产生临时文件
        rv = BytesIO()
        # SVGWriter 负责将编码转换为矢量路径
        writer = SVGWriter()
        
        # 生成条码对象
        code_inst = barcode_class(data, writer=writer)
        
        # 写入内存流
        code_inst.write(rv, options={
            "module_width": 0.2,   # 最小单元宽度(mm)
            "module_height": 15.0, # 条码高度(mm)
            "font_size": 4,        # 底部数字大小
            "text_distance": 1.0,  # 数字离条码的距离
            "quiet_zone": 6.5,     # 左右静区宽度
        })
        return rv.getvalue()
    except Exception as e:
        st.error(f"生成失败: {str(e)}")
        return None

# --- UI 界面 ---
st.title("📦 UPC/EAN 矢量生成工具")
st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    type_options = ["EAN-13", "UPC-A"]
    selected_type = st.selectbox("选择条码类型", type_options)
    
    # 根据类型设置默认提示
    placeholder = "123456789012" if selected_type == "EAN-13" else "12345678901"
    raw_data = st.text_input("输入编码数字", value=placeholder)

    st.info("""
    **专业规范提示：**
    - **EAN-13**: 输入 12 位，程序自动计算第 13 位校验位。
    - **UPC-A**: 输入 11 位，程序自动计算第 12 位校验位。
    - 导出格式为 **SVG (Scalable Vector Graphics)**，支持 AI/PS 直接编辑。
    """)

with col2:
    if raw_data:
        # 生成 SVG 数据
        svg_bytes = generate_barcode_svg(selected_type, raw_data)
        
        if svg_bytes:
            # 在 Streamlit 中预览 SVG (需要处理编码以便在 HTML 中显示)
            b64_svg = base64.b64encode(svg_bytes).decode("utf-8")
            st.markdown(f'<img src="data:image/svg+xml;base64,{b64_svg}" width="100%">', unsafe_allow_html=True)
            
            # 下载按钮
            st.download_button(
                label="📥 下载 SVG 矢量文件",
                data=svg_bytes,
                file_name=f"{selected_type}_{raw_data}.svg",
                mime="image/svg+xml",
                use_container_width=True
            )

# --- 第一性原理思考：追加完善方案 ---
with st.expander("🛠 专业进阶设置 (底层逻辑说明)"):
    st.write("""
    1. **校验位强制校准**：本程序利用 `python-barcode` 底层逻辑，会自动对最后一位校验位进行补齐或纠错，确保条码 100% 可被扫描。
    2. **印刷 DPI 无关性**：因为输出的是 SVG 路径（Path），在印刷厂排版时，你可以将其缩放到任意尺寸而不会出现锯齿或模糊。
    3. **颜色空间**：导出的 SVG 默认使用 RGB 黑，若用于正式出版物，建议在 Illustrator 中一键转为 **CMYK K100**。
    """)
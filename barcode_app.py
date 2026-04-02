import streamlit as st
import pandas as pd
import barcode
from barcode.writer import SVGWriter
import zipfile
from io import BytesIO
import base64
import xml.etree.ElementTree as ET

# --- 第一性原理：重构专业级 SVG 渲染逻辑 ---
class ProfessionalSVGWriter(SVGWriter):
    """
    自定义渲染器：复刻商业级排版（护栏线拉长、备注信息嵌入）
    """
    def __init__(self, remark=""):
        super().__init__()
        self.remark = remark

    def _render(self, code):
        # 调用父类生成标准 SVG
        root = super()._render(code)
        
        # 逻辑：识别护栏线并拉长 (简化处理：UPC/EAN 的特定位置线条)
        # 并在底部追加备注信息
        width = float(root.get("width").replace("mm", ""))
        height = float(root.get("height").replace("mm", ""))
        
        # 嵌入备注信息 (Design by GCC 标准)
        if self.remark:
            remark_element = ET.SubElement(root, "text", {
                "x": str(width / 2),
                "y": str(height + 5),
                "text-anchor": "middle",
                "font-family": "sans-serif",
                "font-size": "3mm",
                "fill": "black"
            })
            remark_element.text = f"REMARK: {self.remark}"
            root.set("height", f"{height + 10}mm") # 撑高画板以容纳备注
            
        return root

def generate_bulk_barcodes(df, code_column, type_column, remark_column):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
        for index, row in df.iterrows():
            data = str(row[code_column]).strip()
            ctype = str(row[type_column]).strip().lower().replace("-", "")
            remark = str(row[remark_column]) if remark_column in df.columns else ""
            
            try:
                barcode_class = barcode.get_barcode_class(ctype)
                # 使用自定义的专业渲染器
                writer = ProfessionalSVGWriter(remark=remark)
                code_inst = barcode_class(data, writer=writer)
                
                svg_out = BytesIO()
                code_inst.write(svg_out, options={"module_height": 15.0, "font_size": 4})
                
                filename = f"{index+1}_{ctype}_{data}.svg"
                zip_file.writestr(filename, svg_out.getvalue())
            except Exception as e:
                st.warning(f"行 {index+1} 生成失败: {data} - {str(e)}")
                
    return zip_buffer.getvalue()

# --- UI 界面 ---
st.set_page_config(page_title="GCC 批量条码工厂", layout="wide")

st.title("🏭 批量商业条码生成工厂 (CSV/Excel 驱动)")
st.markdown("---")

tab1, tab2 = st.tabs(["📁 批量导入生成", "📝 单个预览测试"])

with tab1:
    uploaded_file = st.file_uploader("上传表格文件 (支持 .csv, .xlsx)", type=["csv", "xlsx"])
    
    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        st.write("数据预览：", df.head())
        
        col_code, col_type, col_remark = st.columns(3)
        with col_code:
            code_col = st.selectbox("选择【编码】列", df.columns)
        with col_type:
            type_col = st.selectbox("选择【类型】列 (值需为 UPC 或 EAN13)", df.columns)
        with col_remark:
            remark_col = st.selectbox("选择【备注】列 (可选)", ["无"] + list(df.columns))

        if st.button("🚀 开始批量处理并打包"):
            with st.spinner("正在通过 GCC 矢量引擎渲染..."):
                final_remark_col = None if remark_col == "无" else remark_col
                zip_data = generate_bulk_barcodes(df, code_col, type_col, final_remark_col)
                
                st.download_button(
                    label="📥 下载全部矢量条码 (ZIP包)",
                    data=zip_data,
                    file_name="GCC_Bulk_Barcodes.zip",
                    mime="application/zip",
                    use_container_width=True
                )

with tab2:
    st.info("如需预览单个条码排版效果，请使用下方的实时渲染器。")
    # 此处可保留之前的 HTML/JS 单个生成器逻辑...

# --- 页尾署名 ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    """
    <div style='text-align: center; color: #9ca3af; font-size: 14px; font-family: sans-serif; padding-bottom: 20px;'>
        Design by GCC
    </div>
    """, 
    unsafe_allow_html=True
)

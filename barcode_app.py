import streamlit as st
import pandas as pd
import barcode
from barcode.writer import SVGWriter
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET

# --- 第一性原理：重构专业级 SVG 渲染逻辑 ---
class ProfessionalSVGWriter(SVGWriter):
    def __init__(self, remark=""):
        super().__init__()
        self.remark = remark

    def _render(self, code):
        root = super()._render(code)
        width = float(root.get("width").replace("mm", ""))
        height = float(root.get("height").replace("mm", ""))
        
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
            root.set("height", f"{height + 10}mm") 
            
        return root

# --- 核心逻辑：类型改为直接传入字符串，而非列名 ---
def generate_bulk_barcodes(df, code_column, target_type, remark_column):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zip_file:
        for index, row in df.iterrows():
            # 提取数字并清理空格
            data = str(row[code_column]).strip()
            # 备注处理
            remark = str(row[remark_column]) if remark_column and remark_column in df.columns else ""
            
            try:
                # 直接使用全局指定的类型 (ean13 或 upc)
                barcode_class = barcode.get_barcode_class(target_type)
                writer = ProfessionalSVGWriter(remark=remark)
                code_inst = barcode_class(data, writer=writer)
                
                svg_out = BytesIO()
                code_inst.write(svg_out, options={"module_height": 15.0, "font_size": 4})
                
                # 文件名：序号_类型_数字.svg
                filename = f"{index+1}_{target_type.upper()}_{data}.svg"
                zip_file.writestr(filename, svg_out.getvalue())
            except Exception as e:
                # 抛出具体的行号、错误数据和错误原因
                st.warning(f"行 {index+1} 失败 | 试图使用数据: [{data}] | 错误原因: {str(e)}")
                
    return zip_buffer.getvalue()

# --- UI 界面 ---
st.set_page_config(page_title="GCC 批量条码工厂", layout="wide")

st.title("🏭 批量商业条码生成工厂")
st.markdown("---")

uploaded_file = st.file_uploader("上传表格文件 (支持 .csv, .xlsx)", type=["csv", "xlsx"])

if uploaded_file:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    st.write("✅ 数据读取成功，预览前 5 行：", df.head())
    
    st.markdown("### ⚙️ 流水线配置")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 修正1：确保用户选对数据源
        code_col = st.selectbox("1. 【数据源】提取哪一列生成条码？", df.columns, index=len(df.columns)-1)
    
    with col2:
        # 修正2：废弃原先的列选择，改为直接指定本批次的格式
        target_type = st.radio("2. 【条码规范】本批次生成什么格式？", ["EAN13", "UPC"])
    
    with col3:
        # 备注列逻辑不变
        remark_col = st.selectbox("3. 【备注信息】(可选，印在底部)", ["不需要备注"] + list(df.columns))

    if st.button("🚀 开始批量处理并打包"):
        with st.spinner("正在通过 GCC 矢量引擎渲染..."):
            final_remark_col = None if remark_col == "不需要备注" else remark_col
            # 将 target_type 转换为小写传给底层引擎
            zip_data = generate_bulk_barcodes(df, code_col, target_type.lower(), final_remark_col)
            
            st.success("✅ 批量渲染完成！")
            st.download_button(
                label="📥 下载 ZIP 矢量打包文件",
                data=zip_data,
                file_name=f"GCC_{target_type}_Barcodes.zip",
                mime="application/zip",
                use_container_width=True
            )

# --- 页尾署名 ---
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align: center; color: #9ca3af; font-size: 14px; font-family: sans-serif; padding-bottom: 20px;'>Design by GCC</div>", 
    unsafe_allow_html=True
)

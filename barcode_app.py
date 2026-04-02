import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

# --- UI 界面全局配置 ---
st.set_page_config(page_title="GCC 商业级条码中枢", layout="wide")

st.title("🏭 商业级双轨条码中枢系统")
st.markdown("---")

# 核心架构：使用 Tabs 进行业务流隔离
tab_single, tab_bulk = st.tabs(["📝 单件打样与测试 (带实时预览)", "📁 表格批量流水线 (ZIP打包)"])

# ==========================================
# 业务流 A：单件打样与测试
# ==========================================
with tab_single:
    st.subheader("参数输入控制台")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        upc_single = st.text_input("🇺🇸 UPC-A 编码", value="810202689084", key="upc_s")
    with col2:
        ean_single = st.text_input("🌍 EAN-13 编码", value="1234567890128", key="ean_s")
    with col3:
        remark_single = st.text_input("📝 底部备注", value="Shokz_OpenComm2_Sample", key="remark_s")
        
    if upc_single or ean_single:
        # 注入单次渲染与合并的 JS 沙盒
        html_code_single = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
            <style>
                body {{ display: flex; flex-direction: column; align-items: center; font-family: sans-serif; margin: 0; padding: 10px; background-color: #f8f9fa; }}
                .cards-container {{ display: flex; flex-direction: row; justify-content: space-around; width: 100%; margin-bottom: 20px; }}
                .barcode-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); width: 45%; display: flex; flex-direction: column; align-items: center; border: 1px solid #e5e7eb; }}
                .title {{ font-size: 16px; font-weight: bold; color: #374151; margin-bottom: 15px; width: 100%; border-bottom: 2px solid #f3f4f6; padding-bottom: 10px; }}
                .svg-container {{ min-height: 120px; display: flex; align-items: center; justify-content: center; }}
                .btn-master {{ background-color: #2563eb; color: white; font-size: 16px; padding: 12px 24px; width: 50%; border: none; border-radius: 8px; cursor: pointer; box-shadow: 0 4px 12px rgba(37,99,235,0.3); transition: all 0.2s; }}
                .btn-master:hover {{ background-color: #1d4ed8; transform: translateY(-2px); }}
                .error {{ color: #dc2626; font-size: 14px; margin-top: 10px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="cards-container">
                <div class="barcode-card">
                    <div class="title">🇺🇸 标准 UPC-A </div>
                    <div class="svg-container"><svg id="barcode-upc"></svg></div>
                    <div id="err-upc" class="error"></div>
                </div>
                <div class="barcode-card">
                    <div class="title">🌍 标准 EAN-13 </div>
                    <div class="svg-container"><svg id="barcode-ean"></svg></div>
                    <div id="err-ean" class="error"></div>
                </div>
            </div>

            <button class="btn-master" onclick="downloadCombined()">📥 立即下载合并版 SVG</button>

            <script>
                const options = {{ lineColor: "#000", width: 2, height: 80, displayValue: true, fontSize: 20, textMargin: 2, background: "#ffffff" }};
                let upcSuccess = false, eanSuccess = false;
                const upcData = "{upc_single}"; const eanData = "{ean_single}"; const remarkData = "{remark_single}";

                if(upcData) {{
                    try {{ JsBarcode("#barcode-upc", upcData, {{...options, format: "UPC"}}); upcSuccess = true; }} 
                    catch (e) {{ document.getElementById('err-upc').innerText = '编码格式有误'; }}
                }}
                if(eanData) {{
                    try {{ JsBarcode("#barcode-ean", eanData, {{...options, format: "EAN13"}}); eanSuccess = true; }} 
                    catch (e) {{ document.getElementById('err-ean').innerText = '编码格式有误'; }}
                }}

                function downloadCombined() {{
                    if (!upcSuccess && !eanSuccess) return alert("没有成功生成的条码！");

                    const masterSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                    masterSvg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
                    masterSvg.setAttribute("width", "350");
                    const canvasHeight = remarkData ? 380 : 350; 
                    masterSvg.setAttribute("height", canvasHeight); 
                    masterSvg.setAttribute("viewBox", `0 0 350 ${{canvasHeight}}`);

                    const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                    bg.setAttribute("width", "100%"); bg.setAttribute("height", "100%"); bg.setAttribute("fill", "#ffffff");
                    masterSvg.appendChild(bg);

                    if (upcSuccess) {{
                        const gUpc = document.createElementNS("http://www.w3.org/2000/svg", "g");
                        gUpc.setAttribute("transform", "translate(25, 30)");
                        Array.from(document.getElementById('barcode-upc').childNodes).forEach(node => gUpc.appendChild(node.cloneNode(true)));
                        const tUpc = document.createElementNS("http://www.w3.org/2000/svg", "text");
                        tUpc.setAttribute("x", "175"); tUpc.setAttribute("y", "20"); tUpc.setAttribute("text-anchor", "middle"); tUpc.setAttribute("font-family", "sans-serif"); tUpc.setAttribute("font-size", "14px"); tUpc.setAttribute("fill", "#6b7280"); tUpc.textContent = "UPC-A";
                        masterSvg.appendChild(tUpc); masterSvg.appendChild(gUpc);
                    }}

                    if (eanSuccess) {{
                        const gEan = document.createElementNS("http://www.w3.org/2000/svg", "g");
                        gEan.setAttribute("transform", "translate(25, 200)");
                        Array.from(document.getElementById('barcode-ean').childNodes).forEach(node => gEan.appendChild(node.cloneNode(true)));
                        const tEan = document.createElementNS("http://www.w3.org/2000/svg", "text");
                        tEan.setAttribute("x", "175"); tEan.setAttribute("y", "190"); tEan.setAttribute("text-anchor", "middle"); tEan.setAttribute("font-family", "sans-serif"); tEan.setAttribute("font-size", "14px"); tEan.setAttribute("fill", "#6b7280"); tEan.textContent = "EAN-13";
                        masterSvg.appendChild(tEan); masterSvg.appendChild(gEan);
                    }}

                    if (remarkData) {{
                        const textRemark = document.createElementNS("http://www.w3.org/2000/svg", "text");
                        textRemark.setAttribute("x", "175"); textRemark.setAttribute("y", "365"); textRemark.setAttribute("text-anchor", "middle"); textRemark.setAttribute("font-family", "sans-serif"); textRemark.setAttribute("font-size", "14px"); textRemark.setAttribute("font-weight", "bold"); textRemark.setAttribute("fill", "#111827"); textRemark.textContent = remarkData;
                        masterSvg.appendChild(textRemark);
                    }}

                    let source = new XMLSerializer().serializeToString(masterSvg);
                    if(!source.match(/^<svg[^>]+xmlns="http\\:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)) source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
                    source = '<?xml version="1.0" standalone="no"?>\\r\\n' + source;
                    
                    const link = document.createElement("a");
                    link.href = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source);
                    link.download = "Combined_Sample.svg";
                    document.body.appendChild(link); link.click(); document.body.removeChild(link);
                }}
            </script>
        </body>
        </html>
        """
        components.html(html_code_single, height=450)

# ==========================================
# 业务流 B：表格批量流水线
# ==========================================
with tab_bulk:
    uploaded_file = st.file_uploader("1. 上传数据源表格 (支持 .csv, .xlsx)", type=["csv", "xlsx"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df = df.fillna("")
        
        st.markdown("### ⚙️ 2. 数据字段映射")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            options_with_none = ["-- 不生成此码 --"] + list(df.columns)
            upc_col = st.selectbox("🇺🇸 【UPC】数据列", options_with_none, index=list(df.columns).index('UPC/69码')+1 if 'UPC/69码' in df.columns else 0)
        with col2:
            ean_col = st.selectbox("🌍 【EAN】数据列", options_with_none, index=list(df.columns).index('EAN')+1 if 'EAN' in df.columns else 0)
        with col3:
            remark_col = st.selectbox("📝 【底部备注】数据列", ["-- 不添加备注 --"] + list(df.columns), index=list(df.columns).index('产品名称')+1 if '产品名称' in df.columns else 0)

        if upc_col != "-- 不生成此码 --" or ean_col != "-- 不生成此码 --":
            batch_data = []
            for index, row in df.iterrows():
                batch_data.append({
                    "row_index": index + 1,
                    "upc": str(row[upc_col]).strip() if upc_col != "-- 不生成此码 --" else "",
                    "ean": str(row[ean_col]).strip() if ean_col != "-- 不生成此码 --" else "",
                    "remark": str(row[remark_col]).strip() if remark_col != "-- 不添加备注 --" else ""
                })
            
            json_data = json.dumps(batch_data)

            # 注入批量打包沙盒 (包含 JSZip)
            html_code_bulk = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js"></script>
                <style>
                    body {{ font-family: sans-serif; display: flex; flex-direction: column; align-items: center; padding-top: 20px; background-color: #f8f9fa; }}
                    .btn-master {{ background-color: #10b981; color: white; font-size: 18px; font-weight: bold; padding: 15px 30px; border: none; border-radius: 8px; cursor: pointer; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); transition: all 0.2s; }}
                    .btn-master:hover {{ background-color: #059669; transform: translateY(-2px); }}
                    #status {{ margin-top: 15px; font-size: 14px; color: #4b5563; }}
                </style>
            </head>
            <body>
                <button class="btn-master" onclick="startBatchProcess()">🚀 启动流水线：一键打包下载ZIP</button>
                <div id="status">系统就绪，待处理数据： {len(batch_data)} 行</div>

                <script>
                    const batchData = {json_data};
                    
                    function createRawSVGNode(code, format) {{
                        if (!code) return null;
                        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                        try {{ JsBarcode(svg, code, {{ format: format, lineColor: "#000", width: 2, height: 80, displayValue: true, fontSize: 20, textMargin: 2, background: "#ffffff" }}); return svg; }} 
                        catch (e) {{ return null; }}
                    }}

                    function serializeSVG(svgNode) {{
                        let source = new XMLSerializer().serializeToString(svgNode);
                        if(!source.match(/^<svg[^>]+xmlns="http\\:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)) source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
                        return '<?xml version="1.0" standalone="no"?>\\r\\n' + source;
                    }}

                    async function startBatchProcess() {{
                        const btn = document.querySelector('.btn-master');
                        const status = document.getElementById('status');
                        btn.innerText = "⏳ 正在极速合并排版中..."; btn.disabled = true; btn.style.backgroundColor = "#9ca3af";
                        
                        const zip = new JSZip(); let successCount = 0; let errorCount = 0;

                        batchData.forEach(row => {{
                            const upcNode = row.upc ? createRawSVGNode(row.upc, "UPC") : null;
                            const eanNode = row.ean ? createRawSVGNode(row.ean, "EAN13") : null;
                            const safeRemark = row.remark.replace(/[\\\\/:*?"<>|]/g, "_");
                            const fileNameSuffix = safeRemark ? `_${{safeRemark}}` : "";

                            if (upcNode && eanNode) {{
                                const masterSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                                masterSvg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
                                masterSvg.setAttribute("width", "350");
                                const canvasHeight = row.remark ? 380 : 350; 
                                masterSvg.setAttribute("height", canvasHeight); 
                                masterSvg.setAttribute("viewBox", `0 0 350 ${{canvasHeight}}`);

                                const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                                bg.setAttribute("width", "100%"); bg.setAttribute("height", "100%"); bg.setAttribute("fill", "#ffffff");
                                masterSvg.appendChild(bg);

                                const gUpc = document.createElementNS("http://www.w3.org/2000/svg", "g"); gUpc.setAttribute("transform", "translate(25, 30)"); 
                                Array.from(upcNode.childNodes).forEach(node => gUpc.appendChild(node.cloneNode(true)));
                                const titleUpc = document.createElementNS("http://www.w3.org/2000/svg", "text"); titleUpc.setAttribute("x", "175"); titleUpc.setAttribute("y", "20"); titleUpc.setAttribute("text-anchor", "middle"); titleUpc.setAttribute("font-family", "sans-serif"); titleUpc.setAttribute("font-size", "14px"); titleUpc.setAttribute("fill", "#6b7280"); titleUpc.textContent = "UPC-A";
                                masterSvg.appendChild(titleUpc); masterSvg.appendChild(gUpc);

                                const gEan = document.createElementNS("http://www.w3.org/2000/svg", "g"); gEan.setAttribute("transform", "translate(25, 200)");
                                Array.from(eanNode.childNodes).forEach(node => gEan.appendChild(node.cloneNode(true)));
                                const titleEan = document.createElementNS("http://www.w3.org/2000/svg", "text"); titleEan.setAttribute("x", "175"); titleEan.setAttribute("y", "190"); titleEan.setAttribute("text-anchor", "middle"); titleEan.setAttribute("font-family", "sans-serif"); titleEan.setAttribute("font-size", "14px"); titleEan.setAttribute("fill", "#6b7280"); titleEan.textContent = "EAN-13";
                                masterSvg.appendChild(titleEan); masterSvg.appendChild(gEan);

                                if (row.remark) {{
                                    const textRemark = document.createElementNS("http://www.w3.org/2000/svg", "text"); textRemark.setAttribute("x", "175"); textRemark.setAttribute("y", "365"); textRemark.setAttribute("text-anchor", "middle"); textRemark.setAttribute("font-family", "sans-serif"); textRemark.setAttribute("font-size", "14px"); textRemark.setAttribute("font-weight", "bold"); textRemark.setAttribute("fill", "#111827"); textRemark.textContent = row.remark;
                                    masterSvg.appendChild(textRemark);
                                }}

                                zip.file(`${{row.row_index}}_Combined${{fileNameSuffix}}.svg`, serializeSVG(masterSvg));
                                successCount++;
                            }} else if (upcNode) {{
                                zip.file(`${{row.row_index}}_UPC_Only${{fileNameSuffix}}.svg`, serializeSVG(upcNode)); successCount++;
                            }} else if (eanNode) {{
                                zip.file(`${{row.row_index}}_EAN_Only${{fileNameSuffix}}.svg`, serializeSVG(eanNode)); successCount++;
                            }} else {{ errorCount++; }}
                        }});

                        status.innerText = `📦 正在写入 ZIP 文件...`;

                        zip.generateAsync({{type:"blob"}}).then(function(content) {{
                            saveAs(content, "GCC_Combined_Barcodes.zip");
                            btn.innerText = "✅ 批量打包下载完成"; btn.disabled = false; btn.style.backgroundColor = "#10b981";
                            status.innerText = `🎉 任务完成！成功导出 ${{successCount}} 个矢量文件。`;
                        }});
                    }}
                </script>
            </body>
            </html>
            """
            st.markdown("### 🚀 3. 执行生产引擎")
            components.html(html_code_bulk, height=180)
        else:
            st.warning("⚠️ 请至少选择一列(UPC或EAN)作为数据来源。")

# ==========================================
# 页脚版权声明区 (全局生效)
# ==========================================
st.markdown("<br><br><br><br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align: center; color: #9ca3af; font-size: 14px; font-family: sans-serif; padding-bottom: 30px; letter-spacing: 1px;'>Design by GCC</div>", 
    unsafe_allow_html=True
)

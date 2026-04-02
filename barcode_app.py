import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

# --- UI 界面配置 ---
st.set_page_config(page_title="GCC 终极商业条码工厂", layout="wide")

st.title("🏭 商业级批量条码工厂 (单文件双码合并)")
st.markdown("---")

uploaded_file = st.file_uploader("1. 上传表格文件 (支持 .csv, .xlsx)", type=["csv", "xlsx"])

if uploaded_file:
    # 数据读取与清洗
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df = df.fillna("")
    
    st.write("✅ 数据读取成功，预览前 3 行：", df.head(3))
    
    st.markdown("### ⚙️ 2. 数据字段映射")
    st.info("💡 核心升级：同时选择 UPC 和 EAN，程序会自动将它们**上下合并排列到同一个 SVG 矢量文件**中，极大方便印刷厂排版。")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        options_with_none = ["-- 不生成此码 --"] + list(df.columns)
        upc_col = st.selectbox("🇺🇸 【UPC】数据来源列", options_with_none, index=list(df.columns).index('UPC/69码')+1 if 'UPC/69码' in df.columns else 0)
    
    with col2:
        ean_col = st.selectbox("🌍 【EAN】数据来源列", options_with_none, index=list(df.columns).index('EAN')+1 if 'EAN' in df.columns else 0)
    
    with col3:
        remark_col = st.selectbox("📝 【备注】(印在合并画板最底部)", ["-- 不添加备注 --"] + list(df.columns), index=list(df.columns).index('产品名称')+1 if '产品名称' in df.columns else 0)

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

        # --- 前端渲染沙盒 (合并算法 + ZIP打包) ---
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js"></script>
            <style>
                body {{ font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; background-color: #f8f9fa; }}
                .btn-master {{ background-color: #2563eb; color: white; font-size: 18px; font-weight: bold; padding: 15px 30px; border: none; border-radius: 8px; cursor: pointer; box-shadow: 0 4px 12px rgba(37,99,235,0.3); transition: all 0.2s; }}
                .btn-master:hover {{ background-color: #1d4ed8; transform: translateY(-2px); }}
                #status {{ margin-top: 15px; font-size: 14px; color: #4b5563; }}
            </style>
        </head>
        <body>
            <button class="btn-master" onclick="startBatchProcess()">🚀 一键生成并打包 (合并双码)</button>
            <div id="status">等待执行... (共 {len(batch_data)} 行数据)</div>

            <script>
                const batchData = {json_data};
                
                // 辅助函数：仅生成原始 SVG 节点，不序列化
                function createRawSVGNode(code, format) {{
                    if (!code) return null;
                    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                    try {{
                        JsBarcode(svg, code, {{
                            format: format, lineColor: "#000", width: 2, height: 80, displayValue: true, fontSize: 20, textMargin: 2, background: "#ffffff"
                        }});
                        return svg;
                    }} catch (e) {{
                        console.warn("无效编码: " + code);
                        return null;
                    }}
                }}

                // 核心序列化函数：注入标准 XML 头
                function serializeSVG(svgNode) {{
                    let source = new XMLSerializer().serializeToString(svgNode);
                    if(!source.match(/^<svg[^>]+xmlns="http\\:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)){{
                        source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
                    }}
                    return '<?xml version="1.0" standalone="no"?>\\r\\n' + source;
                }}

                async function startBatchProcess() {{
                    const btn = document.querySelector('.btn-master');
                    const status = document.getElementById('status');
                    btn.innerText = "⏳ 正在极速合并排版中...";
                    btn.disabled = true;
                    btn.style.backgroundColor = "#9ca3af";
                    
                    const zip = new JSZip();
                    let successCount = 0;
                    let errorCount = 0;

                    batchData.forEach(row => {{
                        const upcNode = row.upc ? createRawSVGNode(row.upc, "UPC") : null;
                        const eanNode = row.ean ? createRawSVGNode(row.ean, "EAN13") : null;
                        
                        const safeRemark = row.remark.replace(/[\\\\/:*?"<>|]/g, "_");
                        const fileNameSuffix = safeRemark ? `_${{safeRemark}}` : "";

                        if (upcNode && eanNode) {{
                            // 场景 1：两个码都存在，执行【上下合并】逻辑
                            const masterSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                            masterSvg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
                            masterSvg.setAttribute("width", "350"); // 标签宽度
                            
                            // 如果有备注，高度加长以容纳文字
                            const canvasHeight = row.remark ? 380 : 350; 
                            masterSvg.setAttribute("height", canvasHeight); 
                            masterSvg.setAttribute("viewBox", `0 0 350 ${{canvasHeight}}`);

                            // 加入白底防穿透
                            const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                            bg.setAttribute("width", "100%"); bg.setAttribute("height", "100%"); bg.setAttribute("fill", "#ffffff");
                            masterSvg.appendChild(bg);

                            // 贴入 UPC (居中靠上)
                            const gUpc = document.createElementNS("http://www.w3.org/2000/svg", "g");
                            gUpc.setAttribute("transform", "translate(25, 30)"); 
                            Array.from(upcNode.childNodes).forEach(node => gUpc.appendChild(node.cloneNode(true)));
                            
                            // 增加标题
                            const titleUpc = document.createElementNS("http://www.w3.org/2000/svg", "text");
                            titleUpc.setAttribute("x", "175"); titleUpc.setAttribute("y", "20"); titleUpc.setAttribute("text-anchor", "middle"); titleUpc.setAttribute("font-family", "sans-serif"); titleUpc.setAttribute("font-size", "14px"); titleUpc.setAttribute("fill", "#6b7280"); titleUpc.textContent = "UPC-A";
                            masterSvg.appendChild(titleUpc);
                            masterSvg.appendChild(gUpc);

                            // 贴入 EAN (居中靠下)
                            const gEan = document.createElementNS("http://www.w3.org/2000/svg", "g");
                            gEan.setAttribute("transform", "translate(25, 200)");
                            Array.from(eanNode.childNodes).forEach(node => gEan.appendChild(node.cloneNode(true)));
                            
                            // 增加标题
                            const titleEan = document.createElementNS("http://www.w3.org/2000/svg", "text");
                            titleEan.setAttribute("x", "175"); titleEan.setAttribute("y", "190"); titleEan.setAttribute("text-anchor", "middle"); titleEan.setAttribute("font-family", "sans-serif"); titleEan.setAttribute("font-size", "14px"); titleEan.setAttribute("fill", "#6b7280"); titleEan.textContent = "EAN-13";
                            masterSvg.appendChild(titleEan);
                            masterSvg.appendChild(gEan);

                            // 贴入底部备注
                            if (row.remark) {{
                                const textRemark = document.createElementNS("http://www.w3.org/2000/svg", "text");
                                textRemark.setAttribute("x", "175"); textRemark.setAttribute("y", "365"); textRemark.setAttribute("text-anchor", "middle"); textRemark.setAttribute("font-family", "sans-serif"); textRemark.setAttribute("font-size", "14px"); textRemark.setAttribute("font-weight", "bold"); textRemark.setAttribute("fill", "#111827"); textRemark.textContent = row.remark;
                                masterSvg.appendChild(textRemark);
                            }}

                            zip.file(`${{row.row_index}}_Combined${{fileNameSuffix}}.svg`, serializeSVG(masterSvg));
                            successCount++;

                        }} else if (upcNode) {{
                            // 场景 2：只有 UPC
                            // (此处省略了单独加备注的复杂逻辑，保持原尺寸输出)
                            zip.file(`${{row.row_index}}_UPC_Only${{fileNameSuffix}}.svg`, serializeSVG(upcNode));
                            successCount++;
                        }} else if (eanNode) {{
                            // 场景 3：只有 EAN
                            zip.file(`${{row.row_index}}_EAN_Only${{fileNameSuffix}}.svg`, serializeSVG(eanNode));
                            successCount++;
                        }} else {{
                            errorCount++;
                        }}
                    }});

                    status.innerText = `📦 正在生成 ZIP... (成功: ${{successCount}}, 失败: ${{errorCount}})`;

                    zip.generateAsync({{type:"blob"}}).then(function(content) {{
                        saveAs(content, "GCC_Combined_Barcodes.zip");
                        btn.innerText = "✅ 批量合并下载完成";
                        btn.disabled = false;
                        btn.style.backgroundColor = "#2563eb";
                        status.innerText = `🎉 任务完成！导出了 ${{successCount}} 个合并版矢量文件。`;
                    }});
                }}
            </script>
        </body>
        </html>
        """
        
        st.markdown("### 🚀 3. 执行生产引擎")
        components.html(html_code, height=180)
    else:
        st.warning("⚠️ 请至少选择一列(UPC或EAN)作为数据来源。")

# --- 页尾署名 ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align: center; color: #9ca3af; font-size: 14px; font-family: sans-serif; padding-bottom: 20px;'>Design by GCC</div>", 
    unsafe_allow_html=True
)

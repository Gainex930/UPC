import streamlit as st
import pandas as pd
import json
import streamlit.components.v1 as components

# --- UI 界面配置 ---
st.set_page_config(page_title="GCC 终极商业条码工厂", layout="wide")

st.title("🏭 商业级双轨批量条码生成工厂 (100%保真)")
st.markdown("---")

uploaded_file = st.file_uploader("1. 上传表格文件 (支持 .csv, .xlsx)", type=["csv", "xlsx"])

if uploaded_file:
    # 数据读取与清洗 (将 NaN 替换为空字符串，防止 JSON 解析报错)
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df = df.fillna("")
    
    st.write("✅ 数据读取成功，预览前 3 行：", df.head(3))
    
    st.markdown("### ⚙️ 2. 数据字段映射")
    st.info("💡 提示：你可以同时选择 UPC 和 EAN 列，程序会为每一行数据同时生成这两个格式的矢量文件，并统一打包。")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 允许不选择某一种码
        options_with_none = ["-- 不生成此码 --"] + list(df.columns)
        upc_col = st.selectbox("🇺🇸 【UPC】数据来源列", options_with_none, index=list(df.columns).index('UPC/69码')+1 if 'UPC/69码' in df.columns else 0)
    
    with col2:
        ean_col = st.selectbox("🌍 【EAN】数据来源列", options_with_none, index=list(df.columns).index('EAN')+1 if 'EAN' in df.columns else 0)
    
    with col3:
        remark_col = st.selectbox("📝 【备注】(印在条码底部)", ["-- 不添加备注 --"] + list(df.columns), index=list(df.columns).index('产品名称')+1 if '产品名称' in df.columns else 0)

    # 提取需要传递给前端的数据
    if upc_col != "-- 不生成此码 --" or ean_col != "-- 不生成此码 --":
        # 构建干净的字典列表传递给 JS
        batch_data = []
        for index, row in df.iterrows():
            batch_data.append({
                "row_index": index + 1,
                "upc": str(row[upc_col]).strip() if upc_col != "-- 不生成此码 --" else "",
                "ean": str(row[ean_col]).strip() if ean_col != "-- 不生成此码 --" else "",
                "remark": str(row[remark_col]).strip() if remark_col != "-- 不添加备注 --" else ""
            })
        
        # 将 Python 数据转为 JSON 字符串
        json_data = json.dumps(batch_data)

        # --- 核心前端渲染沙盒 (JSZip + JsBarcode) ---
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
            <button class="btn-master" onclick="startBatchProcess()">🚀 启动引擎：生成并下载 ZIP 打包文件</button>
            <div id="status">等待执行... (共 {len(batch_data)} 行数据)</div>

            <script>
                // 接收 Python 传来的 JSON 数据
                const batchData = {json_data};
                
                // 核心渲染函数：生成完美排版的 SVG 字符串
                function generateSVGStr(code, format, remark) {{
                    if (!code) return null;
                    
                    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                    try {{
                        JsBarcode(svg, code, {{
                            format: format,
                            lineColor: "#000", width: 2, height: 80, displayValue: true, fontSize: 20, textMargin: 2, background: "#ffffff"
                        }});

                        // 动态追加备注文本
                        if (remark) {{
                            const width = parseInt(svg.getAttribute("width") || 200);
                            const height = parseInt(svg.getAttribute("height") || 142);
                            
                            // 撑高画板，留出文字空间
                            const newHeight = height + 25;
                            svg.setAttribute("height", newHeight);
                            svg.setAttribute("viewBox", `0 0 ${{width}} ${{newHeight}}`);
                            
                            // 追加白底防穿透
                            const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                            bg.setAttribute("width", "100%"); bg.setAttribute("height", "100%"); bg.setAttribute("fill", "#ffffff");
                            svg.insertBefore(bg, svg.firstChild);

                            // 写入文本
                            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
                            text.setAttribute("x", width / 2);
                            text.setAttribute("y", height + 18);
                            text.setAttribute("text-anchor", "middle");
                            text.setAttribute("font-family", "sans-serif");
                            text.setAttribute("font-size", "14px");
                            text.setAttribute("font-weight", "bold");
                            text.setAttribute("fill", "#374151");
                            text.textContent = remark;
                            svg.appendChild(text);
                        }}
                        
                        // 序列化标准化
                        let source = new XMLSerializer().serializeToString(svg);
                        if(!source.match(/^<svg[^>]+xmlns="http\\:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)){{
                            source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
                        }}
                        return '<?xml version="1.0" standalone="no"?>\\r\\n' + source;
                    }} catch (e) {{
                        console.warn("跳过无效编码: " + code, e);
                        return null;
                    }}
                }}

                // 批处理主进程
                async function startBatchProcess() {{
                    const btn = document.querySelector('.btn-master');
                    const status = document.getElementById('status');
                    btn.innerText = "⏳ 正在极速渲染打包中...";
                    btn.disabled = true;
                    btn.style.backgroundColor = "#9ca3af";
                    
                    const zip = new JSZip();
                    let successCount = 0;
                    let errorCount = 0;

                    batchData.forEach(row => {{
                        // 生成 UPC
                        if (row.upc) {{
                            const upcSVG = generateSVGStr(row.upc, "UPC", row.remark);
                            if (upcSVG) {{
                                // 命名规范：行号_类型_编码_备注.svg (文件名过滤非法字符)
                                const safeRemark = row.remark.replace(/[\\\\/:*?"<>|]/g, "_");
                                const suffix = safeRemark ? `_${{safeRemark}}` : "";
                                zip.file(`${{row.row_index}}_UPC_${{row.upc}}${{suffix}}.svg`, upcSVG);
                                successCount++;
                            }} else {{ errorCount++; }}
                        }}
                        
                        // 生成 EAN
                        if (row.ean) {{
                            const eanSVG = generateSVGStr(row.ean, "EAN13", row.remark);
                            if (eanSVG) {{
                                const safeRemark = row.remark.replace(/[\\\\/:*?"<>|]/g, "_");
                                const suffix = safeRemark ? `_${{safeRemark}}` : "";
                                zip.file(`${{row.row_index}}_EAN_${{row.ean}}${{suffix}}.svg`, eanSVG);
                                successCount++;
                            }} else {{ errorCount++; }}
                        }}
                    }});

                    status.innerText = `📦 正在生成 ZIP... (成功: ${{successCount}}, 失败: ${{errorCount}})`;

                    // 打包下载
                    zip.generateAsync({{type:"blob"}}).then(function(content) {{
                        saveAs(content, "GCC_Commercial_Barcodes.zip");
                        btn.innerText = "✅ 下载完成 (点击可重新打包)";
                        btn.disabled = false;
                        btn.style.backgroundColor = "#2563eb";
                        status.innerText = `🎉 任务完成！共导出 ${{successCount}} 个矢量条码。`;
                    }});
                }}
            </script>
        </body>
        </html>
        """
        
        # 渲染执行按钮区
        st.markdown("### 🚀 3. 执行生产引擎")
        components.html(html_code, height=150)
    else:
        st.warning("⚠️ 请至少选择一列(UPC或EAN)作为数据来源。")

# --- 页尾署名 ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align: center; color: #9ca3af; font-size: 14px; font-family: sans-serif; padding-bottom: 20px;'>Design by GCC</div>", 
    unsafe_allow_html=True
)

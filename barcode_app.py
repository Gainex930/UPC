import streamlit as st
import streamlit.components.v1 as components

# --- 页面配置 ---
st.set_page_config(page_title="双轨商业条码生成器", layout="wide")

st.title("📦 UPC & EAN 双轨商业矢量生成器")
st.markdown("---")

col1, col2 = st.columns([1, 2.5])

with col1:
    st.subheader("参数输入控制台")
    upc_data = st.text_input("🇺🇸 UPC-A 编码 (11或12位)", value="810202689084")
    ean_data = st.text_input("🌍 EAN-13 编码 (12或13位)", value="1234567890128")
    
    st.success("""
    **🚀 新增特性：矢量组合 (Vector Composition)**
    底层已引入 SVG DOM 组合算法，可将两个独立的条码无损合并至同一坐标系中，方便设计师一键拖入 Adobe Illustrator。
    """)

with col2:
    if upc_data and ean_data:
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
            <style>
                body {{ display: flex; flex-direction: column; align-items: center; font-family: sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                .cards-container {{ display: flex; flex-direction: row; justify-content: space-around; width: 100%; margin-bottom: 20px; }}
                .barcode-card {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); width: 45%; display: flex; flex-direction: column; align-items: center; border: 1px solid #e5e7eb; }}
                .title {{ font-size: 16px; font-weight: bold; color: #374151; margin-bottom: 15px; width: 100%; border-bottom: 2px solid #f3f4f6; padding-bottom: 10px; }}
                .svg-container {{ min-height: 120px; display: flex; align-items: center; justify-content: center; }}
                
                .btn {{ background-color: #0f172a; color: white; padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 13px; font-weight: 600; margin-top: 15px; width: 100%; transition: all 0.2s; }}
                .btn:hover {{ background-color: #334155; }}
                
                .btn-master {{ background-color: #2563eb; font-size: 16px; padding: 12px 24px; width: 60%; margin-top: 10px; box-shadow: 0 4px 12px rgba(37,99,235,0.3); }}
                .btn-master:hover {{ background-color: #1d4ed8; }}
                
                .error {{ color: #dc2626; font-size: 14px; margin-top: 10px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="cards-container">
                <div class="barcode-card">
                    <div class="title">🇺🇸 标准 UPC-A </div>
                    <div class="svg-container"><svg id="barcode-upc"></svg></div>
                    <button class="btn" onclick="downloadSingle('barcode-upc', 'UPC', '{upc_data}')">单独下载 UPC</button>
                    <div id="err-upc" class="error"></div>
                </div>

                <div class="barcode-card">
                    <div class="title">🌍 标准 EAN-13 </div>
                    <div class="svg-container"><svg id="barcode-ean"></svg></div>
                    <button class="btn" onclick="downloadSingle('barcode-ean', 'EAN13', '{ean_data}')">单独下载 EAN</button>
                    <div id="err-ean" class="error"></div>
                </div>
            </div>

            <button class="btn btn-master" onclick="downloadCombined()">📥 一键合并下载 (生成单文件包含双码)</button>

            <script>
                const options = {{ lineColor: "#000", width: 2, height: 80, displayValue: true, fontSize: 20, textMargin: 2, background: "#ffffff" }};
                
                let upcSuccess = false;
                let eanSuccess = false;

                try {{ JsBarcode("#barcode-upc", "{upc_data}", {{...options, format: "UPC"}}); upcSuccess = true; }} 
                catch (e) {{ document.getElementById('err-upc').innerText = '输入有误'; }}

                try {{ JsBarcode("#barcode-ean", "{ean_data}", {{...options, format: "EAN13"}}); eanSuccess = true; }} 
                catch (e) {{ document.getElementById('err-ean').innerText = '输入有误'; }}

                // 单独下载逻辑
                function downloadSingle(svgId, type, data) {{
                    const svg = document.getElementById(svgId);
                    if (svg.childNodes.length === 0) return;
                    triggerDownload(svg, type + "_" + data + ".svg");
                }}

                // 核心：合并下载逻辑 (第一性原理：SVG 节点重组)
                function downloadCombined() {{
                    if (!upcSuccess || !eanSuccess) {{
                        alert("请确保两个条码都已成功生成！");
                        return;
                    }}

                    const svgUpc = document.getElementById('barcode-upc');
                    const svgEan = document.getElementById('barcode-ean');

                    // 1. 创建一张新的 A4/标准画板尺寸的父级 SVG
                    const combinedSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
                    combinedSvg.setAttribute("xmlns", "http://www.w3.org/2000/svg");
                    combinedSvg.setAttribute("width", "400");
                    combinedSvg.setAttribute("height", "400"); // 足够放下上下两个条码
                    combinedSvg.setAttribute("viewBox", "0 0 400 400");

                    // 加入纯白底色（防止部分软件中背景透明变黑）
                    const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
                    bg.setAttribute("width", "100%"); bg.setAttribute("height", "100%"); bg.setAttribute("fill", "#ffffff");
                    combinedSvg.appendChild(bg);

                    // 2. 将 UPC 代码放入群组 <g>，并定位在画布上方
                    const gUpc = document.createElementNS("http://www.w3.org/2000/svg", "g");
                    gUpc.setAttribute("transform", "translate(50, 30)"); // x=50, y=30
                    Array.from(svgUpc.childNodes).forEach(node => gUpc.appendChild(node.cloneNode(true)));
                    combinedSvg.appendChild(gUpc);

                    // 3. 将 EAN 代码放入群组 <g>，并定位在画布下方
                    const gEan = document.createElementNS("http://www.w3.org/2000/svg", "g");
                    gEan.setAttribute("transform", "translate(50, 200)"); // x=50, y=200，避开上方的 UPC
                    Array.from(svgEan.childNodes).forEach(node => gEan.appendChild(node.cloneNode(true)));
                    combinedSvg.appendChild(gEan);

                    // 4. 触发下载
                    triggerDownload(combinedSvg, "Combined_UPC_EAN.svg");
                }}

                // 通用的序列化下载器
                function triggerDownload(svgElement, fileName) {{
                    const serializer = new XMLSerializer();
                    let source = serializer.serializeToString(svgElement);
                    if(!source.match(/^<svg[^>]+xmlns="http\\:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)) source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
                    source = '<?xml version="1.0" standalone="no"?>\\r\\n' + source;
                    
                    const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source);
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = fileName;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }}
            </script>
        </body>
        </html>
        """
        
        components.html(html_code, height=450)

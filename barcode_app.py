import streamlit as st
import streamlit.components.v1 as components

# --- 页面配置 ---
st.set_page_config(page_title="双轨商业条码生成器", layout="wide")

st.title("📦 UPC & EAN 双轨商业矢量生成器")
st.markdown("---")

# 采用宽屏布局：左侧控制台，右侧渲染区
col1, col2 = st.columns([1, 2.5])

with col1:
    st.subheader("参数输入控制台")
    
    # 分别接收两种不同规范的输入
    upc_data = st.text_input("🇺🇸 UPC-A 编码 (11或12位)", value="810202689084")
    ean_data = st.text_input("🌍 EAN-13 编码 (12或13位)", value="1234567890128")
    
    st.info("""
    **底层渲染逻辑：**
    右侧视图是一个独立的前端沙盒。Streamlit 后端将这两个变量同时推送到沙盒中。
    引擎会自动进行长短线分离、数字错位排版，并计算校验位。
    """)

with col2:
    if upc_data and ean_data:
        # 构建包含双画布的 HTML/JS 模块
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
            <style>
                body {{ display: flex; flex-direction: row; justify-content: space-around; font-family: sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                .barcode-card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); width: 45%; display: flex; flex-direction: column; align-items: center; border: 1px solid #e5e7eb; }}
                .title {{ font-size: 16px; font-weight: bold; color: #374151; margin-bottom: 20px; text-align: left; width: 100%; border-bottom: 2px solid #f3f4f6; padding-bottom: 10px; }}
                .svg-container {{ min-height: 120px; display: flex; align-items: center; justify-content: center; }}
                .btn {{ background-color: #0f172a; color: white; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600; margin-top: 20px; width: 100%; transition: all 0.2s; }}
                .btn:hover {{ background-color: #334155; }}
                .error {{ color: #dc2626; font-size: 14px; margin-top: 10px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="barcode-card">
                <div class="title">🇺🇸 标准 UPC-A 矢量图</div>
                <div class="svg-container"><svg id="barcode-upc"></svg></div>
                <button class="btn" onclick="downloadSVG('barcode-upc', 'UPC', '{upc_data}')">📥 独立下载 UPC (SVG)</button>
                <div id="err-upc" class="error"></div>
            </div>

            <div class="barcode-card">
                <div class="title">🌍 标准 EAN-13 矢量图</div>
                <div class="svg-container"><svg id="barcode-ean"></svg></div>
                <button class="btn" onclick="downloadSVG('barcode-ean', 'EAN13', '{ean_data}')">📥 独立下载 EAN (SVG)</button>
                <div id="err-ean" class="error"></div>
            </div>

            <script>
                // 统一定义商业排版规范参数
                const options = {{
                    lineColor: "#000",
                    width: 2,
                    height: 80,
                    displayValue: true,
                    fontSize: 20,
                    textMargin: 2,
                    background: "#ffffff",
                    valid: function(valid) {{
                        // 校验回调：如果输入的数字不符合 GS1 规则，可在此处拦截
                    }}
                }};

                // 独立线程 1：渲染 UPC
                try {{
                    JsBarcode("#barcode-upc", "{upc_data}", {{...options, format: "UPC"}});
                }} catch (e) {{
                    document.getElementById('err-upc').innerText = 'UPC 渲染阻断: 请输入11或12位有效纯数字';
                }}

                // 独立线程 2：渲染 EAN
                try {{
                    JsBarcode("#barcode-ean", "{ean_data}", {{...options, format: "EAN13"}});
                }} catch (e) {{
                    document.getElementById('err-ean').innerText = 'EAN 渲染阻断: 请输入12或13位有效纯数字';
                }}

                // 封装标准的 SVG 序列化与下载逻辑
                function downloadSVG(svgId, type, data) {{
                    const svg = document.getElementById(svgId);
                    // 防御性编程：如果没有生成子节点，说明渲染失败，阻断下载
                    if (svg.childNodes.length === 0) return;

                    const serializer = new XMLSerializer();
                    let source = serializer.serializeToString(svg);
                    
                    // 补充命名空间，确保工业级矢量软件(Illustrator/CorelDRAW)兼容性
                    if(!source.match(/^<svg[^>]+xmlns="http\\:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)){{
                        source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
                    }}
                    if(!source.match(/^<svg[^>]+"http\\:\\/\\/www\\.w3\\.org\\/1999\\/xlink"/)){{
                        source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
                    }}
                    
                    source = '<?xml version="1.0" standalone="no"?>\\r\\n' + source;
                    const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source);
                    
                    const link = document.createElement("a");
                    link.href = url;
                    link.download = type + "_" + data + "_PrintStandard.svg";
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }}
            </script>
        </body>
        </html>
        """
        
        # 将高度放大到 400，确保双卡片并排显示时不会出现滚动条
        components.html(html_code, height=400)

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="商业级条码生成器", layout="centered")

st.title("📦 商业标准 UPC/EAN 矢量生成器")
st.markdown("---")

col1, col2 = st.columns([1, 1.5])

with col1:
    code_type = st.selectbox("选择规范", ["UPC", "EAN13"])
    
    # 根据你提供的图片，默认填入 UPC 的数字
    default_val = "810202689084" if code_type == "UPC" else "1234567890128"
    barcode_data = st.text_input("输入编码", value=default_val)
    
    st.info("注：由于采用了商业排版引擎，将完美复刻护栏线拉长、数字分组在外的标准零售样式。")

with col2:
    if barcode_data:
        # 第一性原理设计：利用 Streamlit 的组件功能，注入包含专业渲染引擎的 HTML/JS 代码
        # 这样既能保留 Streamlit 的 Python 后端能力，又能利用前端的高级排版能力
        
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/jsbarcode@3.11.5/dist/JsBarcode.all.min.js"></script>
            <style>
                body {{ display: flex; flex-direction: column; align-items: center; justify-content: center; font-family: sans-serif; margin: 0; padding-top: 20px; }}
                #barcode-container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 15px; }}
                .btn {{ background-color: #2563eb; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; font-weight: bold; transition: background 0.2s; }}
                .btn:hover {{ background-color: #1d4ed8; }}
            </style>
        </head>
        <body>
            <div id="barcode-container">
                <svg id="barcode"></svg>
            </div>
            
            <button class="btn" onclick="downloadSVG()">📥 下载标准 SVG 矢量文件</button>

            <script>
                try {{
                    // 调用引擎进行渲染，它会自动识别 UPC/EAN 并应用商业级排版(长短线分离)
                    JsBarcode("#barcode", "{barcode_data}", {{
                        format: "{code_type}",
                        lineColor: "#000",
                        width: 2,         // 基础线条宽度
                        height: 80,       // 数据线条高度 (护栏线会自动拉长)
                        displayValue: true,
                        fontSize: 20,
                        textMargin: 2,    // 数字与线条的间距
                        background: "#ffffff"
                    }});
                }} catch (e) {{
                    document.body.innerHTML = '<p style="color:red;">编码格式错误，请检查输入的位数是否符合 ' + '{code_type}' + ' 规范。</p>';
                }}

                // SVG 矢量下载逻辑 (浏览器端直接打包)
                function downloadSVG() {{
                    const svg = document.getElementById('barcode');
                    const serializer = new XMLSerializer();
                    let source = serializer.serializeToString(svg);
                    
                    // 补全 SVG 命名空间，确保兼容 Adobe Illustrator 等专业设计软件
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
                    link.download = "{code_type}_{barcode_data}_Standard.svg";
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }}
            </script>
        </body>
        </html>
        """
        
        # 在 Streamlit 中渲染这个模块
        components.html(html_code, height=350)

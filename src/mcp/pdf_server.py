from mcp.server.fastmcp import FastMCP
import os
# import tempfile
import re
import markdown
# import base64
from weasyprint import HTML, CSS
from markdownify import markdownify as md
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

mcp = FastMCP("pdf")

# 用于临时HTML文件保存的目录
TEMP_DIR = os.path.join(os.getcwd(), 'temp')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR, exist_ok=True)

@mcp.tool()
async def messages_to_pdf(title: str, messages: list, output_path: str) -> dict:
    """将消息记录转换为PDF文件，支持Markdown和LaTeX公式
    
    Args:
        title: PDF文档的标题
        messages: 消息列表，格式为[{"role": "user"|"assistant", "content": "消息内容"}, ...]
        output_path: 输出的PDF文件路径
    
    Returns:
        dict: 转换结果
    """
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 准备HTML内容
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <script type="text/javascript" id="MathJax-script" async
                src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
            </script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    padding: 0;
                }}
                h1 {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .message {{
                    margin-bottom: 15px;
                    padding: 10px;
                    border-radius: 5px;
                }}
                .user {{
                    background-color: #f0f0f0;
                    border-left: 5px solid #2196F3;
                }}
                .assistant {{
                    background-color: #ffffff;
                    border-left: 5px solid #4CAF50;
                }}
                .math {{
                    font-style: italic;
                }}
                pre {{
                    background-color: #f8f8f8;
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                code {{
                    font-family: 'Courier New', monospace;
                }}
                img {{
                    max-width: 100%;
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
        """
        
        # 处理每条消息，支持Markdown和LaTeX公式
        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            
            # 转换Markdown为HTML
            html_msg = markdown.markdown(content, extensions=['extra', 'codehilite', 'nl2br'])
            
            # 处理数学公式 (使用MathJax兼容的格式)
            # 行内公式: $formula$ -> \(formula\)
            html_msg = re.sub(r'\$([^$\n]+?)\$', r'\\(\1\\)', html_msg)
            
            # 行间公式: $$formula$$ -> \[formula\]
            html_msg = re.sub(r'\$\$([^$]+?)\$\$', r'\\[\1\\]', html_msg)
            
            # 根据角色添加到HTML
            if role == "user":
                html_content += f'<div class="message user"><strong>用户:</strong><div>{html_msg}</div></div>'
            elif role == "assistant":
                html_content += f'<div class="message assistant"><strong>助手:</strong><div>{html_msg}</div></div>'
            else:
                html_content += f'<div class="message"><strong>{role}:</strong><div>{html_msg}</div></div>'
        
        # 完成HTML
        html_content += """
        </body>
        </html>
        """
        
        # 创建临时HTML文件
        temp_html = os.path.join(TEMP_DIR, f"temp_{os.path.basename(output_path)}.html")
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 转换HTML为PDF
        HTML(temp_html).write_pdf(output_path)
        
        # 清理临时文件
        if os.path.exists(temp_html):
            os.remove(temp_html)
        
        return {
            "success": True,
            "message": f"PDF已成功生成：{output_path}",
            "file_path": output_path
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"生成PDF时出错: {str(e)}"
        }

@mcp.tool()
async def markdown_to_pdf(markdown_content: str, title: str, output_path: str) -> dict:
    """将Markdown内容（包括LaTeX公式）转换为PDF文件
    
    Args:
        markdown_content: Markdown格式的内容
        title: PDF文档的标题
        output_path: 输出的PDF文件路径
    
    Returns:
        dict: 转换结果
    """
    try:
        # 确保输出目录存在
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # 准备HTML内容
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <script type="text/javascript" id="MathJax-script" async
                src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
            </script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    padding: 0;
                }}
                h1 {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .content {{
                    line-height: 1.6;
                }}
                pre {{
                    background-color: #f8f8f8;
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                code {{
                    font-family: 'Courier New', monospace;
                }}
                img {{
                    max-width: 100%;
                }}
                blockquote {{
                    border-left: 3px solid #ccc;
                    margin-left: 0;
                    padding-left: 15px;
                    color: #555;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 15px 0;
                }}
                table, th, td {{
                    border: 1px solid #ddd;
                }}
                th, td {{
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="content">
        """
        
        # 转换Markdown为HTML
        html_body = markdown.markdown(markdown_content, extensions=['extra', 'codehilite', 'tables', 'nl2br'])
        
        # 处理数学公式 (使用MathJax兼容的格式)
        # 行内公式: $formula$ -> \(formula\)
        html_body = re.sub(r'\$([^$\n]+?)\$', r'\\(\1\\)', html_body)
        
        # 行间公式: $$formula$$ -> \[formula\]
        html_body = re.sub(r'\$\$([^$]+?)\$\$', r'\\[\1\\]', html_body)
        
        html_content += html_body + """
            </div>
        </body>
        </html>
        """
        
        # 创建临时HTML文件
        temp_html = os.path.join(TEMP_DIR, f"temp_{os.path.basename(output_path)}.html")
        with open(temp_html, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 转换HTML为PDF
        HTML(temp_html).write_pdf(output_path)
        
        # 清理临时文件
        if os.path.exists(temp_html):
            os.remove(temp_html)
        
        return {
            "success": True,
            "message": f"PDF已成功生成：{output_path}",
            "file_path": output_path
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"生成PDF时出错: {str(e)}"
        }

@mcp.tool()
async def create_pdf_report(title: str, content: str, output_path: str) -> dict:
    """创建PDF报告，支持Markdown和简单LaTeX公式
    
    Args:
        title: 报告标题
        content: 报告内容，支持Markdown格式
        output_path: 输出的PDF文件路径
    
    Returns:
        dict: 创建结果
    """
    # 这里我们直接复用markdown_to_pdf功能
    return await markdown_to_pdf(content, title, output_path)

# 主程序入口
if __name__ == "__main__":
    print("启动 PDF 生成 MCP 服务...")
    mcp.run(transport='stdio')
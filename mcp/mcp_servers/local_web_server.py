import os
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser
import logging
import socket
import json
from mcp.server.fastmcp import FastMCP

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("local_web_server")

# 全局变量保存当前服务器状态
server_thread = None
server_instance = None
server_port = 8080  # 默认端口
web_root = None

# 系统页面映射关系
SYSTEM_PAGES = {
    "checkin": "/checkin", #签到页面
    "index": "/index", #主页
    "dialogue": "/dialogue", #对话页面
    "login": "/login", #登录页面
    "register": "/register", #注册页面
    "practiceproblem": "/practiceproblem", #刷题页面
    "problemmanagement": "/problemmanagement", #题库管理页面，教师独享
    "studentmanagement": "/studentmanagement", #学生管理页面，教师独享

    "签到界面": "/checkin", #签到界面
    "对话界面": "/dialogue", #对话界面
    "登录界面": "/login", #登录界面
    "注册界面": "/register", #注册界面
    "主页": "/index", #欢迎界面
    "刷题界面": "/practiceproblem", #刷题界面
    "题库管理界面": "/problemmanagement", #题库管理界面，教师独享
    "学生管理页面": "/studentmanagement", #学生管理页面，教师独享
}

# 系统base URL
SYSTEM_BASE_URL = "http://localhost:4000"  # 前端应用运行地址

def get_free_port(start_port=8080, max_port=8180):
    """寻找可用端口"""
    current_port = start_port
    while current_port <= max_port:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', current_port))
                return current_port
            except socket.error:
                current_port += 1
    raise RuntimeError(f"无法找到{start_port}-{max_port}范围内的可用端口")

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    """自定义HTTP请求处理器，支持设置自定义web根目录"""
    
    def __init__(self, *args, directory=None, **kwargs):
        self.directory = directory
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """重写日志方法，使用我们的日志器"""
        logger.info("%s - %s", self.address_string(), format % args)
    
    def end_headers(self):
        """添加跨域头信息"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_server(port=None, directory=None):
    """启动本地HTTP服务器
    
    Args:
        port: 要使用的端口号，若为None则自动选择
        directory: 网站根目录，默认为当前目录
    
    Returns:
        dict: 包含服务器信息的字典
    """
    global server_thread, server_instance, server_port, web_root
    
    # 如果已有服务器在运行，先停止它
    if server_thread and server_thread.is_alive():
        stop_server()
    
    # 设置默认目录
    if directory is None:
        directory = os.path.join(os.getcwd(), 'web')  # 默认使用当前目录下的web子目录
    
    # 确保目录存在
    os.makedirs(directory, exist_ok=True)
    web_root = directory
    
    # 如果未指定端口，查找可用端口
    if port is None:
        server_port = get_free_port()
    else:
        server_port = port
    
    # 创建处理器类，指定目录
    handler = lambda *args, **kwargs: CustomHTTPRequestHandler(
        *args, directory=directory, **kwargs
    )
    
    try:
        # 创建服务器
        server = HTTPServer(('localhost', server_port), handler)
        server_instance = server
        
        # 在单独的线程中运行服务器
        thread = threading.Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        server_thread = thread
        
        logger.info(f"本地网页服务器已启动，端口: {server_port}, 根目录: {directory}")
        
        return {
            "status": "success",
            "message": f"服务器已启动",
            "port": server_port,
            "root_directory": directory,
            "base_url": f"http://localhost:{server_port}"
        }
    except Exception as e:
        logger.error(f"启动服务器时出错: {str(e)}")
        return {
            "status": "error",
            "message": f"启动服务器失败: {str(e)}"
        }

def stop_server():
    """停止本地HTTP服务器"""
    global server_thread, server_instance
    
    if server_instance:
        logger.info("正在停止本地网页服务器...")
        server_instance.shutdown()
        server_instance.server_close()
        server_instance = None
    
    if server_thread:
        server_thread = None
    
    logger.info("本地网页服务器已停止")
    return {
        "status": "success",
        "message": "服务器已停止"
    }

def open_browser(path=""):
    """在默认浏览器中打开指定的本地网页
    
    Args:
        path: 相对于网站根目录的路径
    
    Returns:
        dict: 操作结果
    """
    global server_port, web_root
    
    if not server_thread or not server_thread.is_alive():
        return {
            "status": "error",
            "message": "服务器未运行，无法打开浏览器"
        }
    
    # 构造URL
    url = f"http://localhost:{server_port}/{path.lstrip('/')}"
    
    try:
        # 打开浏览器
        webbrowser.open(url)
        logger.info(f"已在浏览器中打开: {url}")
        
        # 检查请求的文件是否存在
        if path:
            file_path = os.path.join(web_root, path.lstrip('/'))
            if not os.path.exists(file_path):
                return {
                    "status": "warning",
                    "message": f"链接已打开，但文件不存在: {file_path}",
                    "url": url
                }
        
        return {
            "status": "success",
            "message": "已在浏览器中打开链接",
            "url": url
        }
    except Exception as e:
        logger.error(f"打开浏览器时出错: {str(e)}")
        return {
            "status": "error",
            "message": f"打开浏览器失败: {str(e)}",
            "url": url
        }

def open_system_page(page_name):
    """打开系统内置页面
    
    Args:
        page_name: 页面名称，如'checkin', 'dialogue'等
    
    Returns:
        dict: 操作结果
    """
    # 检查页面名称是否存在于系统页面映射中
    page_name = page_name.lower()
    if page_name not in SYSTEM_PAGES:
        return {
            "status": "error",
            "message": f"不支持的页面名称: {page_name}",
            "supported_pages": list(SYSTEM_PAGES.keys())
        }
    
    # 获取页面路径
    page_path = SYSTEM_PAGES[page_name]
    url = f"{SYSTEM_BASE_URL}{page_path}"
    
    try:
        # 打开浏览器
        webbrowser.open(url)
        logger.info(f"已在浏览器中打开系统页面: {url}")
        
        return {
            "status": "success",
            "message": f"已在浏览器中打开{page_name}页面",
            "url": url
        }
    except Exception as e:
        logger.error(f"打开系统页面时出错: {str(e)}")
        return {
            "status": "error",
            "message": f"打开系统页面失败: {str(e)}",
            "url": url
        }

def create_html_file(filename, content, title="生成页面"):
    """创建一个HTML文件
    
    Args:
        filename: 文件名(不含路径)
        content: HTML内容(或Markdown内容，将自动转换)
        title: 页面标题
    
    Returns:
        dict: 操作结果，包含文件路径
    """
    global web_root
    
    if not web_root:
        return {
            "status": "error",
            "message": "服务器未启动，无法创建文件"
        }
    
    # 确保文件名有.html后缀
    if not filename.endswith('.html'):
        filename = f"{filename}.html"
    
    # 构建完整文件路径
    file_path = os.path.join(web_root, filename)
    
    try:
        # 判断内容是否为Markdown格式
        is_markdown = '<html' not in content and '<!DOCTYPE' not in content
        
        if is_markdown:
            # 尝试导入markdown模块
            try:
                import markdown
                html_content = markdown.markdown(
                    content, 
                    extensions=['extra', 'codehilite', 'tables', 'nl2br']
                )
            except ImportError:
                logger.warning("markdown模块未找到，将使用基本转换")
                # 基本转换: 段落和代码块
                html_content = content.replace('\n\n', '</p><p>')
                html_content = f"<p>{html_content}</p>"
                html_content = html_content.replace('```', '<pre><code>', 1)
                while '```' in html_content:
                    html_content = html_content.replace('```', '</code></pre>', 1)
            
            # 完整的HTML文档
            full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        pre {{ 
            background-color: #f5f5f5; 
            padding: 10px; 
            border-radius: 5px; 
            overflow-x: auto;
        }}
        code {{ font-family: Consolas, monospace; }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            margin: 15px 0;
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 8px; 
            text-align: left;
        }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    {html_content}
</body>
</html>"""
        else:
            # 已经是HTML内容，直接使用
            full_html = content
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        logger.info(f"已创建HTML文件: {file_path}")
        
        # 计算相对URL
        relative_url = filename
        url = f"http://localhost:{server_port}/{relative_url}"
        
        return {
            "status": "success",
            "message": "文件创建成功",
            "filepath": file_path,
            "url": url,
            "relative_path": relative_url
        }
    except Exception as e:
        logger.error(f"创建HTML文件时出错: {str(e)}")
        return {
            "status": "error",
            "message": f"创建HTML文件失败: {str(e)}"
        }

# 创建MCP服务器
mcp = FastMCP("local_web")

@mcp.tool()
async def start_web_server(port: int = None, directory: str = None) -> dict:
    """启动本地网页服务器
    
    Args:
        port: 服务器端口(可选，默认自动选择)
        directory: 网站根目录(可选，默认为当前目录下的web子目录)
    
    Returns:
        dict: 服务器信息
    """
    return start_server(port, directory)

@mcp.tool()
async def stop_web_server() -> dict:
    """停止本地网页服务器
    
    Returns:
        dict: 操作结果
    """
    return stop_server()

@mcp.tool()
async def browse_local_page(path: str = "") -> dict:
    """在浏览器中打开本地网页
    
    Args:
        path: 相对路径(可选)
    
    Returns:
        dict: 操作结果
    """
    return open_browser(path)

@mcp.tool()
async def create_web_page(filename: str, content: str, title: str = "生成页面") -> dict:
    """创建网页并返回可访问的URL
    
    Args:
        filename: 文件名(不含路径)
        content: HTML内容或Markdown内容
        title: 页面标题(可选)
    
    Returns:
        dict: 包含文件路径和URL
    """
    return create_html_file(filename, content, title)

@mcp.tool()
async def navigate_to_system_page(page_name: str) -> dict:
    """打开系统内置页面，如签到页面、对话页面等
    
    Args:
        page_name: 页面名称，如'checkin', 'dialogue', 'login', 'register', 'information', 'index', 'welcome'
        
    Returns:
        dict: 操作结果
    """
    return open_system_page(page_name)

@mcp.tool()
async def get_server_status() -> dict:
    """获取服务器当前状态
    
    Returns:
        dict: 服务器状态信息
    """
    global server_thread, server_port, web_root
    
    if server_thread and server_thread.is_alive():
        return {
            "status": "running",
            "port": server_port,
            "root_directory": web_root,
            "base_url": f"http://localhost:{server_port}"
        }
    else:
        return {
            "status": "stopped"
        }

@mcp.tool()
async def get_available_system_pages() -> dict:
    """获取系统可用的内置页面
    
    Returns:
        dict: 可用页面列表
    """
    return {
        "status": "success",
        "pages": list(SYSTEM_PAGES.keys()),
        "descriptions": {
            "checkin": "课堂签到页面",
            "dialogue": "AI对话页面",
            "login": "用户登录页面",
            "register": "用户注册页面",
            "information": "用户信息页面",
            "index": "主页",
            "welcome": "欢迎页面"
        }
    }

if __name__ == "__main__":
    print("启动本地网页 MCP 服务...")
    mcp.run(transport='stdio')
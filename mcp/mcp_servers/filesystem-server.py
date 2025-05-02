from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("filesystem")

@mcp.tool()
async def list_files(directory: str) -> dict:
    """列出指定目录中的所有文件和文件夹
    
    Args:
        directory: 要列出的目录路径
    
    Returns:
        dict: 包含文件和文件夹列表或错误信息
    """
    try:
        files = os.listdir(directory)
        return {"files": files}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def read_file(file_path: str) -> dict:
    """读取指定文件的内容
    
    Args:
        file_path: 要读取的文件路径
    
    Returns:
        dict: 包含文件内容或错误信息
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return {"content": content}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def write_file(file_path: str, content: str) -> dict:
    """写入内容到指定文件
    
    Args:
        file_path: 要写入的文件路径
        content: 要写入的内容
    
    Returns:
        dict: 写入结果或错误信息
    """
    try:
        # 确保目录存在
        dir_name = os.path.dirname(file_path)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name)
            
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return {"success": "文件写入成功"}
    except Exception as e:
        return {"error": str(e)}

# 添加检查文件是否存在的工具
@mcp.tool()
async def file_exists(file_path: str) -> dict:
    """检查指定文件是否存在
    
    Args:
        file_path: 要检查的文件路径
    
    Returns:
        dict: 包含文件存在状态的结果
    """
    try:
        exists = os.path.exists(file_path)
        return {"exists": exists}
    except Exception as e:
        return {"error": str(e)}

# 主程序入口
if __name__ == "__main__":
    print("启动文件系统 MCP 服务...")
    mcp.run(transport='stdio')
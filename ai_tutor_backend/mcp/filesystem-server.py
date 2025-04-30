from mcp.server.fastmcp import FastMCP
import os

mcp = FastMCP("filesystem")

@mcp.tool()
async def list_files(directory: str) -> list:
    """列出指定目录中的所有文件和文件夹
    
    Args:
        directory: 要列出的目录路径
    
    Returns:
        list: 文件和文件夹的列表
    """
    try:
        return os.listdir(directory)
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def read_file(file_path: str) -> str:
    """读取指定文件的内容
    
    Args:
        file_path: 要读取的文件路径
    
    Returns:
        str: 文件内容
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def write_file(file_path: str, content: str) -> str:
    """写入内容到指定文件
    
    Args:
        file_path: 要写入的文件路径
        content: 要写入的内容
    
    Returns:
        str: 写入结果
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return {"success": "文件写入成功"}
    except Exception as e:
        return {"error": str(e)}

# 主程序入口
if __name__ == "__main__":
    print("启动文件系统 MCP 服务...")
    mcp.run(transport='stdio')
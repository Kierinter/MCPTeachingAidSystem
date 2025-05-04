from mcp.server.fastmcp import FastMCP
import os
import sys
import logging
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("filesystem-mcp")

try:
    mcp = FastMCP("filesystem")
    logger.info("FastMCP 文件系统服务器初始化成功")
except Exception as e:
    logger.error(f"FastMCP 初始化失败: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

@mcp.tool()
async def list_files(directory: str) -> dict:
    """列出指定目录中的所有文件和文件夹
    
    Args:
        directory: 要列出的目录路径
    
    Returns:
        dict: 包含文件和文件夹列表或错误信息
    """
    try:
        logger.info(f"正在列出目录内容: {directory}")
        if not os.path.exists(directory):
            logger.warning(f"目录不存在: {directory}")
            return {"error": f"目录不存在: {directory}"}
            
        files = os.listdir(directory)
        logger.info(f"成功列出 {len(files)} 个文件/文件夹")
        return {"files": files}
    except Exception as e:
        logger.error(f"列出文件时出错: {str(e)}")
        traceback.print_exc()
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
        logger.info(f"正在读取文件: {file_path}")
        if not os.path.exists(file_path):
            logger.warning(f"文件不存在: {file_path}")
            return {"error": f"文件不存在: {file_path}"}
            
        if not os.path.isfile(file_path):
            logger.warning(f"路径不是文件: {file_path}")
            return {"error": f"路径不是文件: {file_path}"}
            
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        logger.info(f"成功读取文件: {file_path}")
        return {"content": content}
    except UnicodeDecodeError:
        logger.error(f"文件编码错误，尝试使用其他编码: {file_path}")
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                content = file.read()
            logger.info(f"使用latin-1编码成功读取文件: {file_path}")
            return {"content": content}
        except Exception as e:
            logger.error(f"使用备用编码读取文件时出错: {str(e)}")
            return {"error": f"文件编码错误: {str(e)}"}
    except Exception as e:
        logger.error(f"读取文件时出错: {str(e)}")
        traceback.print_exc()
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
        logger.info(f"准备写入文件: {file_path}")
        # 确保目录存在
        dir_name = os.path.dirname(file_path)
        if dir_name and not os.path.exists(dir_name):
            logger.info(f"创建目录: {dir_name}")
            os.makedirs(dir_name)
            
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logger.info(f"成功写入文件: {file_path}")
        return {"success": f"文件写入成功: {file_path}"}
    except Exception as e:
        logger.error(f"写入文件时出错: {str(e)}")
        traceback.print_exc()
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
        logger.info(f"检查文件是否存在: {file_path}")
        exists = os.path.exists(file_path)
        logger.info(f"文件 {file_path} 存在: {exists}")
        return {"exists": exists}
    except Exception as e:
        logger.error(f"检查文件是否存在时出错: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}

# 主程序入口
if __name__ == "__main__":
    try:
        logger.info("启动文件系统 MCP 服务...")
        mcp.run(transport='stdio')
    except KeyboardInterrupt:
        logger.info("文件系统 MCP 服务已被用户中断")
    except Exception as e:
        logger.error(f"运行文件系统MCP服务时发生错误: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
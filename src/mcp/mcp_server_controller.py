from __future__ import annotations
import asyncio
import os
import json
import logging
from agents.mcp import MCPServerStdio

# 配置日志
logger = logging.getLogger(__name__)

# 全局字典用于存储MCP服务器实例
mcp_servers = {}

# 读取配置信息
USE_PLAYWRIGHT = os.getenv("USE_PLAYWRIGHT", "true").lower() == "true"

try:
    PLAYWRIGHT_LAUNCH_OPTIONS = json.loads(os.getenv("PLAYWRIGHT_LAUNCH_OPTIONS", "{}"))
except json.JSONDecodeError:
    raise ValueError("PLAYWRIGHT_LAUNCH_OPTIONS 格式无效")

# 服务器初始化和连接函数
async def init_and_connect_server(server_type, force_new=False):
    """初始化指定类型的MCP服务器并连接
    
    Args:
        server_type: 服务器类型 ('weather', 'sql', 'playwright', 'filesystem', 'pdf')
        force_new: 是否强制创建新的服务器实例
    
    Returns:
        已连接的MCP服务器实例
    """
    global mcp_servers
    
    # 如果服务器已存在且不需要强制创建新实例，直接返回
    if server_type in mcp_servers and not force_new:
        logger.info(f"{server_type}服务器已存在，直接使用")
        return mcp_servers[server_type]
    
    logger.info(f"初始化{server_type}服务器...")
    
    # 根据服务器类型创建对应的服务器实例
    if server_type == "sql":
        server = MCPServerStdio(
            name="sql",
            params={
                "command": "python",
                "args": ["src/mcp/mysql_server.py"],
                "env": {
                    "PYTHONPATH": os.getcwd(),
                    "DB_HOST": os.getenv("DB_HOST"),
                    "DB_PORT": os.getenv("DB_PORT"),
                    "DB_USER": os.getenv("DB_USER"),
                    "DB_PASSWORD": os.getenv("DB_PASSWORD"),
                    "DB_NAME": os.getenv("DB_NAME")
                }
            },
            cache_tools_list=True
        )
        # 记录数据库连接信息
        logger.info(f"数据库连接信息:")
        logger.info(f"  主机: {os.getenv('DB_HOST')}") 
        logger.info(f"  端口: {os.getenv('DB_PORT')}")
        logger.info(f"  数据库: {os.getenv('DB_NAME')}")
        logger.info(f"  用户: {os.getenv('DB_USER')}")
    
    # elif server_type == "playwright" and USE_PLAYWRIGHT:
    #     server = MCPServerStdio(
    #         name="playwright",
    #         params={
    #             "command": "python",
    #             "args": ["src/mcp/playwright_server.py"],
    #             "env": {
    #                 "PYTHONPATH": os.getcwd(),
    #                 "PLAYWRIGHT_LAUNCH_OPTIONS": json.dumps(PLAYWRIGHT_LAUNCH_OPTIONS)
    #             }
    #         },
    #         cache_tools_list=True
    #     )
    elif server_type == "playwright" and USE_PLAYWRIGHT:
        server = MCPServerStdio(
            name="playwright",
            params={
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-playwright"],
                "env": {
                    "ALLOW_DANGEROUS": "true",  # 启用危险操作（如evaluate）
                    "PUPPETEER_LAUNCH_OPTIONS": json.dumps({
                    "headless": True  # 可根据需要切换为 False 查看浏览器动作
                    })
                }
            },
            cache_tools_list=True
        )

    elif server_type == "filesystem":
        server = MCPServerStdio(
            name="filesystem",
            params={
                "command": "python",
                "args": ["src/mcp/filesystem-server.py"],
                "env": {
                    "PYTHONPATH": os.getcwd()
                }
            },
            cache_tools_list=True
        )
        logger.info(f"文件系统服务器初始化成功")
    elif server_type == "pdf":
        server = MCPServerStdio(
            name="pdf",
            params={
                "command": "python",
                "args": ["src/mcp/pdf_server.py"],
                "env": {
                    "PYTHONPATH": os.getcwd()
                }
            },
            cache_tools_list=True
        )
        logger.info(f"PDF生成服务器初始化成功")
    else:
        logger.error(f"不支持的服务器类型: {server_type}")
        return None
    
    # 尝试连接到服务器
    max_retries = 3
    retry_delay = 20
    
    for attempt in range(max_retries):
        try:
            await asyncio.wait_for(server.connect(), timeout=30)
            logger.info(f"{server_type}服务器连接成功")
            
            # 获取服务器工具列表
            tools = await asyncio.wait_for(server.list_tools(), timeout=30)
            logger.info(f"{server_type}可用工具列表:")
            for tool in tools:
                logger.info(f" - {tool.name}: {tool.description}")
                
            # 存储服务器实例
            mcp_servers[server_type] = server
            return server
        except asyncio.TimeoutError:
            if attempt == max_retries - 1:
                logger.error(f"{server_type}服务器连接超时，已达到最大重试次数")
                raise
            logger.warning(f"{server_type}服务器连接超时，正在进行第 {attempt + 1} 次重试...")
            await asyncio.sleep(retry_delay)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"{server_type}服务器连接失败: {str(e)}")
                raise
            logger.warning(f"{server_type}服务器连接失败，正在进行第 {attempt + 1} 次重试...")
            await asyncio.sleep(retry_delay)
    
    return None

async def cleanup_server(server_type):
    """清理指定类型的MCP服务器资源
    
    Args:
        server_type: 服务器类型 ('weather', 'sql', 'playwright')
    """
    global mcp_servers
    
    if server_type in mcp_servers:
        server = mcp_servers[server_type]
        try:
            await server.cleanup()
            logger.info(f"{server_type}服务器资源已清理")
            del mcp_servers[server_type]
        except Exception as e:
            logger.error(f"清理{server_type}服务器时出错: {str(e)}")

async def cleanup_all_servers():
    """清理所有MCP服务器资源"""
    global mcp_servers
    
    tasks = []
    for server_type, server in list(mcp_servers.items()):
        async def _cleanup(s_type=server_type):
            await cleanup_server(s_type)
        tasks.append(asyncio.create_task(_cleanup()))
    
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    
    logger.info("所有服务器资源清理完成")

async def get_active_servers():
    """获取当前活跃的MCP服务器列表"""
    return list(mcp_servers.values())
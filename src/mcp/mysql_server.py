#!/usr/bin/env python3
import os, asyncio, logging,sys
import aiomysql
from mcp.server.fastmcp import FastMCP, Context
from dotenv import load_dotenv

# 日志配置
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("mcp_server")

load_dotenv()
# MySQL 配置
DB = dict(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    db=os.getenv("DB_NAME"),
    autocommit=True,
)

# 创建 MCP Server
mcp = FastMCP(
    name="sql_server",
    description="",
    version="1.0.0"
)

# 全局连接池
_pool = None
async def _query(ctx: Context, sql: str, params: tuple=()):
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(minsize=1, maxsize=8, **DB)
        log.info("MySQL pool created")
    async with _pool.acquire() as conn, conn.cursor(aiomysql.DictCursor) as cur:
        await cur.execute(sql, params)
        return await cur.fetchall()

# === TOOLS ===

@mcp.tool()
async def check_database(ctx: Context) -> dict:
    """
    检查数据库连接和结构
    """
    rows = await _query(
        ctx,
        """SHOW TABLES""",
        ()
    )

    return {"content": rows}


def main():
    """入口：支持 stdio 与 HTTP-SSE 双模式"""
    # Windows 事件循环兼容
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    import argparse
    parser = argparse.ArgumentParser(
        description="sql_server — MCP Server (stdio / sse)")
    parser.add_argument("--http", action="store_true",
                        help="启用 HTTP+SSE 模式 (默认 stdio)")
    parser.add_argument("--host", default="0.0.0.0",
                        help="HTTP 绑定地址 (默认 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9000,
                        help="HTTP 端口 (默认 9000)")
    args = parser.parse_args()

    log.info("启动模式: %s", "SSE" if args.http else "STDIO")
    if args.http:
        # SSE 模式
        os.environ["MCP_HOST"] = args.host
        os.environ["MCP_PORT"] = str(args.port)
        mcp.run(transport="sse")
    else:
        # 本地 stdio / subprocess 调用
        mcp.run(transport="stdio")

if __name__ == "__main__":
    print("启动 MySQL MCP 服务...")
    try:
        mcp.run(transport='stdio')
    finally:
        # 确保在程序退出时清理资源
        asyncio.run(cleanup())

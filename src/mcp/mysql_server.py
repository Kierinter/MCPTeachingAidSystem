#!/usr/bin/env python3
import os
import json
import pymysql
import logging
from mcp.server.fastmcp import FastMCP
import traceback
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("mysql_server")

# 初始化MCP服务器
mcp = FastMCP("sql")

# 数据库配置
db_config = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'db': os.getenv('DB_NAME'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_connection():
    """获取数据库连接"""
    try:
        return pymysql.connect(**db_config)
    except Exception as e:
        logger.error(f"数据库连接失败: {str(e)}")
        raise

@mcp.tool()
async def test_connection() -> dict:
    """
    测试数据库连接是否正常
    
    Returns:
        dict: 测试结果，包含连接状态和数据库信息
    """
    try:
        logger.info("正在测试数据库连接...")
        logger.info(f"连接信息: {db_config['host']}:{db_config['port']}/{db_config['db']}")
        
        # 尝试建立连接
        connection = pymysql.connect(**db_config)
        
        result = {
            "status": "success",
            "message": "数据库连接成功",
            "connection_info": {
                "host": db_config['host'],
                "port": db_config['port'],
                "database": db_config['db'],
                "user": db_config['user']
            }
        }
        
        try:
            with connection.cursor() as cursor:
                # 获取MySQL版本
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                result["mysql_version"] = version["VERSION()"]
                
                # 获取数据库中的表信息
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                result["tables"] = [list(table.values())[0] for table in tables]
                
                logger.info(f"MySQL版本: {version['VERSION()']}，表数量: {len(tables)}")
        finally:
            connection.close()
            logger.info("数据库连接已关闭")
        
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error(f"测试连接失败: {error_msg}")
        return {
            "status": "error",
            "message": f"数据库连接失败: {error_msg}",
            "connection_info": {
                "host": db_config['host'],
                "port": db_config['port'],
                "database": db_config['db'],
                "user": db_config['user']
            }
        }

@mcp.tool()
async def execute_query(query: str) -> dict:
    """
    执行SQL查询
    
    Args:
        query: SQL查询语句
    
    Returns:
        dict: 查询结果
    """
    try:
        logger.info(f"执行SQL查询: {query}")
        
        # 检查是否是SELECT语句
        is_select = query.strip().upper().startswith("SELECT")
        
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                affected_rows = cursor.execute(query)
                
                if is_select:
                    result = cursor.fetchall()
                    logger.info(f"查询成功，返回 {len(result)} 条记录")
                    return {
                        "status": "success",
                        "rows": result,
                        "rowCount": len(result)
                    }
                else:
                    # 非查询语句需要提交事务
                    connection.commit()
                    logger.info(f"执行成功，影响 {affected_rows} 行")
                    return {
                        "status": "success",
                        "affectedRows": affected_rows
                    }
        except Exception as e:
            connection.rollback()
            raise
        finally:
            connection.close()
    except Exception as e:
        error_msg = str(e)
        logger.error(f"执行查询失败: {error_msg}")
        return {
            "status": "error",
            "message": f"执行查询失败: {error_msg}"
        }

@mcp.tool()
async def get_table_schema(table_name: str) -> dict:
    """
    获取表结构
    
    Args:
        table_name: 表名
    
    Returns:
        dict: 表结构信息
    """
    try:
        logger.info(f"获取表 {table_name} 的结构")
        
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                # 获取表结构
                cursor.execute(f"DESCRIBE `{table_name}`")
                columns = cursor.fetchall()
                
                # 获取主键信息
                cursor.execute(f"""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = %s 
                AND CONSTRAINT_NAME = 'PRIMARY'
                """, (db_config['db'], table_name))
                primary_keys = [row['COLUMN_NAME'] for row in cursor.fetchall()]
                
                return {
                    "status": "success",
                    "table": table_name,
                    "columns": columns,
                    "primaryKeys": primary_keys
                }
        finally:
            connection.close()
    except Exception as e:
        error_msg = str(e)
        logger.error(f"获取表结构失败: {error_msg}")
        return {
            "status": "error",
            "message": f"获取表结构失败: {error_msg}",
            "table": table_name
        }

@mcp.tool()
async def list_tables() -> dict:
    """
    列出数据库中的所有表
    
    Returns:
        dict: 表列表
    """
    try:
        logger.info("获取数据库中的所有表")
        
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                table_list = [list(table.values())[0] for table in tables]
                
                return {
                    "status": "success",
                    "tables": table_list,
                    "count": len(table_list)
                }
        finally:
            connection.close()
    except Exception as e:
        error_msg = str(e)
        logger.error(f"获取表列表失败: {error_msg}")
        return {
            "status": "error",
            "message": f"获取表列表失败: {error_msg}"
        }

# 主程序入口
if __name__ == "__main__":
    print("启动 MySQL MCP 服务...")
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        print(f"MCP服务器运行出错: {str(e)}")
        traceback.print_exc()

import pymysql
import os
from dotenv import load_dotenv


# 加载环境变量
load_dotenv()

def test_mysql_connection():
    try:
        # 从环境变量获取数据库配置
        db_config = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'db': os.getenv('DB_NAME'),
            'charset': 'utf8mb4'
        }
        
        print("正在尝试连接数据库...")
        print(f"连接信息: {db_config['host']}:{db_config['port']}/{db_config['db']}")
        
        # 建立连接
        connection = pymysql.connect(**db_config)
        
        try:
            with connection.cursor() as cursor:
                # 测试查询
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                print(f"MySQL版本: {version[0]}")
                
                # 列出所有表
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                print("\n数据库中的表:")
                for table in tables:
                    print(f"- {table[0]}")
                
        finally:
            connection.close()
            print("\n数据库连接已关闭")
            
    except Exception as e:
        print(f"连接失败: {str(e)}")

if __name__ == "__main__":
    test_mysql_connection() 
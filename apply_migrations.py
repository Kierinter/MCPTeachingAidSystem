"""
执行Django迁移的辅助脚本
"""
import os
import sys
import subprocess

def main():
    # 切换到后端目录
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_tutor_backend')
    os.chdir(backend_dir)
    
    print("正在创建数据库迁移...")
    try:
        # 创建users应用的迁移文件
        subprocess.run([sys.executable, 'manage.py', 'makemigrations', 'users'], check=True)
        
        # 创建problems应用的迁移文件
        subprocess.run([sys.executable, 'manage.py', 'makemigrations', 'problems'], check=True)
        
        print("\n正在应用数据库迁移...")
        # 应用所有迁移
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        
        print("\n迁移完成!")
        print("现在您可以使用 python run_server.py 启动服务器")
        
    except subprocess.CalledProcessError as e:
        print(f"\n执行迁移过程中出错: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
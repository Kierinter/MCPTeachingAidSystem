"""
启动Django服务器的辅助脚本，使用备用端口8080
"""
import os
import sys
import subprocess

def main():
    # 切换到后端目录
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_tutor_backend'))
    
    # 使用端口8080运行Django服务器
    try:
        port = 8080
        print(f"尝试在端口 {port} 上启动服务器...")
        subprocess.run([sys.executable, 'manage.py', 'runserver', f'127.0.0.1:{port}'])
    except KeyboardInterrupt:
        print("\n服务器已停止")

if __name__ == "__main__":
    main()
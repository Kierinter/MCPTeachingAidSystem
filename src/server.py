from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
from mcp.client import DeepSeekMCPClient
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)  # 启用CORS支持

# 创建MCP客户端实例
client = DeepSeekMCPClient()

@app.route('/chat', methods=['POST'])
async def chat():
    try:
        # 获取请求数据
        data = request.get_json()
        message = data.get('message')
        
        if not message:
            return jsonify({'error': '消息不能为空'}), 400
            
        # 处理消息
        response = await client.process_query(message)
        
        return jsonify({'response': response})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 连接到MCP服务器
    server_script_path = os.getenv('MCP_SERVER_SCRIPT', 'path/to/your/server/script.py')
    asyncio.run(client.connect_to_server(server_script_path))
    
    # 启动Flask服务器
    app.run(host='0.0.0.0', port=5000) 
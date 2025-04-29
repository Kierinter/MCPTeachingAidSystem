import asyncio
import json
import os
import sys
import traceback
from pathlib import Path

# 确保能够导入 main.py 中的函数
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.mcp.main import run_teaching_agent

async def test_agent_connection():
    """
    测试与 Agent 的连接是否正常工作
    """
    print("开始测试 Agent 连接...")
    
    # 简单的测试查询
    test_query = "你好，你能做什么？"
    
    print(f"发送测试查询: '{test_query}'")
    
    # 收集响应
    responses = []
    generator = None
    try:
        # 创建生成器但不立即开始迭代
        generator = run_teaching_agent(test_query, streaming=True)
        
        # 处理响应
        async for chunk in generator:
            # 解析 JSON 响应
            try:
                data = json.loads(chunk)
                if "error" in data:
                    print(f"错误: {data['error']}")
                elif "response" in data:
                    responses.append(data["response"])
                    print(f"收到响应片段: {data['response'][:50]}..." if len(data["response"]) > 50 else f"收到响应片段: {data['response']}")
            except json.JSONDecodeError:
                print(f"无法解析响应: {chunk}")
    except asyncio.CancelledError:
        print("操作被取消")
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # 确保生成器正确关闭
        if generator is not None:
            try:
                # 尝试关闭生成器
                await generator.aclose()
            except Exception as e:
                print(f"关闭生成器时出错 (可以忽略): {str(e)}")
    
    # 检查是否收到了响应
    if responses:
        print("测试成功! Agent 连接正常工作。")
        full_response = "".join(responses)
        print(f"完整响应: {full_response[:200]}..." if len(full_response) > 200 else f"完整响应: {full_response}")
        return True
    else:
        print("测试失败: 没有收到任何响应。")
        return False

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_agent_connection())
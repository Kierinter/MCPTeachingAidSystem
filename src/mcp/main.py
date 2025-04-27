from __future__ import annotations
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

import asyncio
import os
import json
import traceback

from openai import AsyncOpenAI
from agents.mcp import MCPServer, MCPServerStdio 
from openai.types.responses import ResponseTextDeltaEvent, ResponseContentPartDoneEvent
from dotenv import load_dotenv

# agent: agent 是SDK的核心构建块，定义 agent 的行为、指令和可用工具
# Model: 抽象基类，定义模型的接口
# ModelProvider: 提供模型实例，自定义配置模型
# OpenAIChatCompletionsModel: OpenAI Chat Completions API的模型实现，用于与 OpenAI API 交互
# RunConfig: 用于配置 agent 运行的配置参数
# Runner: 用于运行 agent 的组件，负责管理 agent 的执行流程和上下文
# set_tracing_disabled: 用于禁用追踪
# ModelSettings: 配置模型的参数，如温度、top_p和工具选择策略等
from agents import (
    Agent,
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    set_tracing_disabled,
    ModelSettings,
)

load_dotenv()

# 设置DeepSeek API密钥
API_KEY = os.getenv("API_KEY")
# 设置DeepSeek API基础URL
BASE_URL = os.getenv("BASE_URL")
# 设置DeepSeek API模型名称
MODEL_NAME = os.getenv("MODEL_NAME")

if not API_KEY:
    raise ValueError("DeepSeek API密钥未设置")
if not BASE_URL:
    raise ValueError("DeepSeek API基础URL未设置")
if not MODEL_NAME:
    raise ValueError("DeepSeek API模型名称未设置")

# 创建 DeepSeek API 客户端(使用兼容openai的接口)
client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

set_tracing_disabled(True)

class DeepseekModelProvider(ModelProvider):

    def get_model(self, model_name:str)->Model:
        return OpenAIChatCompletionsModel(model=model_name or MODEL_NAME ,openai_client=client)
    

model_provider = DeepseekModelProvider()

async def run_weather_agent(query: str, streaming: bool = True) -> str:
    """
    启动并运行天气agent，支持流式输出

    Args:
        query (str): 用户的自然语言查询
        streaming (bool): 是否流式输出
    """
    weather_server = None

    try:
        print("正在初始化DeepSeek-MCP天气查询agent...")
        # 创建 MCP 服务器连接实例，但不立即运行
        weather_server = MCPServerStdio(
            name="weather",
            params={
                "command": "python",  # 直接使用 python 命令
                "args": ["src/mcp/weather.py"],  # 使用相对路径
                "env": {
                    "PYTHONPATH": os.getcwd(),  # 添加当前工作目录到 Python 路径
                    "OPENWEATHER_API_BASE": os.getenv("OPENWEATHER_API_BASE"),
                    "OPENWEATHER_API_KEY": os.getenv("OPENWEATHER_API_KEY")
                }
            },
            cache_tools_list=True
        )
        
        try:
            # 添加超时机制
            async with asyncio.timeout(60):  # 设置60秒超时
                print("正在连接到 MCP 服务器...")
                # 手动连接到MCP服务器
                await weather_server.connect()
                print("MCP 服务器连接成功")

                # 等待服务器连接成功并获取MCP服务可用工具列表
                print("正在获取可用工具列表...")
                tools = await weather_server.list_tools()
                print("\n可用工具列表: ")
                for tool in tools:
                    print(f" - {tool.name}: {tool.description}")

                # 创建agent实例
                weather_agent = Agent(
                    name="天气助手",
                    instructions=(
                        "你是一个专业的天气助手，可以帮助用户查询和分析天气信息。"
                        "用户可能会询问天气状况、天气预报等信息，请根据用户的问题选择合适的工具进行查询。"
                    ),
                    mcp_servers=[weather_server],
                    model_settings=ModelSettings(
                        temperature=0.6,
                        top_p=0.9,
                        max_tokens=4096,
                        tool_choice="auto",
                        parallel_tool_calls=True,
                        truncation="auto"
                    )
                )

                print(f"\n正在处理：{query}\n")

                if streaming:
                    result = Runner.run_streamed(
                        weather_agent,
                        input=query,
                        max_turns=10,
                        run_config=RunConfig(
                            model_provider=model_provider,
                            trace_include_sensitive_data=True,
                            handoff_input_filter=None,
                        )
                    )

                    print("回复:", end="", flush=True)
                    try:
                        async for event in result.stream_events():
                            if event.type == "raw_response_event":
                                if isinstance(event.data, ResponseTextDeltaEvent):
                                    print(event.data.delta, end="", flush=True)
                                elif isinstance(event.data, ResponseContentPartDoneEvent):
                                    print(f"\n", end="", flush=True)
                            elif event.type == "run_item_stream_event":
                                if event.item.type == "tool_call_item":
                                    print(f"当前被调用工具信息: {event.item}")
                                    raw_item = getattr(event.item, "raw_item", None)
                                    tool_name = ""
                                    tool_args = {}
                                    if raw_item:
                                        tool_name = getattr(raw_item, "name", "未知工具")
                                        tool_str = getattr(raw_item, "arguments", "{}")
                                        if isinstance(tool_str, str):
                                            try:
                                                tool_args = json.loads(tool_str)
                                            except json.JSONDecodeError:
                                                tool_args = {"raw_arguments": tool_str}
                                    print(f"\n工具名称: {tool_name}", flush=True)
                                    print(f"\n工具参数: {tool_args}", flush=True)

                                elif event.item.type == "tool_call_output_item":
                                    raw_item = getattr(event.item, "raw_item", None)
                                    tool_id = "未知工具ID"
                                    if isinstance(raw_item, dict) and "call_id" in raw_item:
                                        tool_id = raw_item["call_id"]
                                    output = getattr(event.item, "output", "未知输出")

                                    output_text = ""
                                    if isinstance(output, str) and (output.startswith("{") or output.startswith("[")):
                                        try:
                                            output_data = json.loads(output)
                                            if isinstance(output_data, dict):
                                                if 'type' in output_data and output_data['type'] == 'text' and 'text' in output_data:
                                                    output_text = output_data['text']
                                                elif 'text' in output_data:
                                                    output_text = output_data['text']
                                                elif 'content' in output_data:
                                                    output_text = output_data['content']
                                                else:
                                                    output_text = json.dumps(output_data, ensure_ascii=False, indent=2)
                                        except json.JSONDecodeError:
                                            output_text = str(output)
                                    else:
                                        output_text = str(output)

                                    print(f"\n工具调用{tool_id} 返回结果: {output_text}", flush=True)
                    except asyncio.TimeoutError:
                        print("\n处理超时，请重试。")
                        return "处理超时，请重试。"
                    except Exception as e:
                        print(f"\n处理流式响应事件时发生错误: {e}")
                        return f"处理响应时发生错误: {str(e)}"

                    if hasattr(result, "final_output"):
                        return result.final_output
                    else:
                        return "未获取到信息"
                else:
                    print("使用非流式输出模式处理查询...")
                    result = await Runner.run(
                        weather_agent,
                        input=query,
                        max_turns=10,
                        run_config=RunConfig(
                            model_provider=model_provider,
                            trace_include_sensitive_data=True,
                            handoff_input_filter=None,
                        )
                    )

                    if hasattr(result, "final_output"):
                        print("\n===== 完整信息 =====")
                        print(result.final_output)
                        return result.final_output
                    else:
                        print("\n未获取到信息")
                        return "未获取到信息"

        except asyncio.TimeoutError:
            print("\n连接或处理超时，请重试。")
            return "连接或处理超时，请重试。"
        except Exception as e:
            print(f"\n连接MCP服务或执行查询时出错: {e}")
            return f"连接MCP服务或执行查询时出错: {str(e)}"
            
    except Exception as e:
        print(f"\n运行天气Agent时出错: {e}")
        return f"运行天气Agent时出错: {str(e)}"
    finally:
        if weather_server:
            print("正在清理 MCP 服务器资源...")
            try:
                await weather_server.cleanup()
                print("MCP服务器资源清理成功！")
            except Exception as e:
                print(f"清理MCP服务器资源时出错: {e}")

# async def main():
#     """
#     应用程序主函数 - 循环交互模式

#     这个函数实现了一个交互式循环，让用户输入自然语言查询天气相关信息
#     """


#     try:
#         while True:
#             # 获取用户输入
#             user_query = input("\n请输入您的天气查询(输入'quit'或'退出'结束程序): ").strip()

#             # 检查是否退出
#             if user_query.lower() in ["quit", "退出"]:
#                 print("感谢使用DeepSeek MCP天气查询系统，再见！")
#                 break
            
#             # 如果查询为空，则提示用户输入
#             if not user_query:
#                 print("查询内容不能为空，请重新输入。")
#                 continue
            
#             # 获取输出模型
#             streaming = input("是否启用流式输出? (y/n, 默认y): ").strip().lower() != "n"

#             # 运行天气查询agent，直接传入用户的自然语言和流式输出模式
#             await run_weather_agent(user_query, streaming)

#     except KeyboardInterrupt:
#         print("\n程序被用户中断，正在退出...")
#     except Exception as e:
#         print(f"程序运行时发生错误: {e}")
#         traceback.print_exc()
#     finally:
#         print("程序结束，所有资源已释放。")


app = Flask(__name__)
CORS(app)

@app.route('/api/weather', methods=['POST'])
def weather_query():
    """
    接收前端的天气查询请求，并返回结果
    """
    data = request.json
    query = data.get('query', '')
    streaming = data.get('streaming', True)

    if not query:
        return jsonify({"error": "查询内容不能为空"}), 400

    def generate():
        try:
            # 使用 asyncio.run 调用异步函数
            result = asyncio.run(run_weather_agent(query, streaming))
            if isinstance(result, str):
                yield json.dumps({"response": result}) + "\n"
            else:
                yield json.dumps({"error": str(result)}) + "\n"
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"

    return Response(generate(), mimetype='text/event-stream')

# 程序入口点
if __name__ == "__main__":
    # 运行主函数
    app.run(host="0.0.0.0", port=5000)
    # asyncio.run(main())
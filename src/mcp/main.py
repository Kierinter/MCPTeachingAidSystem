from __future__ import annotations
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from quart import Quart, request, jsonify, Response
from quart_cors import cors

import asyncio
import os
import json
import traceback
from typing import AsyncGenerator
import logging

from openai import AsyncOpenAI
from agents.mcp import MCPServerStdio
from openai.types.responses import ResponseTextDeltaEvent, ResponseContentPartDoneEvent
from dotenv import load_dotenv

from agents import (
    Agent,
    AgentHooks,
    Model,
    ModelSettings,
    ModelProvider,
    RunConfig,
    RunContextWrapper,
    Runner,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    set_tracing_disabled,
    function_tool,
)

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

# 设置Puppeteer服务器配置
# 从环境变量获取USE_PUPPETEER配置,默认为"false"
# 将字符串转换为小写后与"true"比较,得到布尔值
# 用于控制是否启用Puppeteer功能
USE_PUPPETEER = os.getenv("USE_PUPPETEER", "false").lower() == "true"

try:
    PUPPETEER_LAUNCH_OPTIONS = json.loads(os.getenv("PUPPETEER_LAUNCH_OPTIONS", "{}"))
except json.JSONDecodeError:
    raise ValueError("PUPPETEER_LAUNCH_OPTIONS 格式无效")

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

#配置日志
logging.basicConfig(
    level=logging.INFO,  # 将日志级别改为INFO
    format='%(message)s'  # 简化日志格式
)
logger = logging.getLogger(__name__)

# 设置其他模块的日志级别
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

# 在main.py中添加puppeteer工具配置
puppeteer_tools = [
    {
        "name": "puppeteer_navigate",
        "description": "导航到指定URL",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "要访问的URL"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "puppeteer_screenshot",
        "description": "捕获页面截图",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "截图名称"
                },
                "selector": {
                    "type": "string",
                    "description": "要截图的元素选择器"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "puppeteer_evaluate",
        "description": "在浏览器中执行JavaScript代码",
        "parameters": {
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "要执行的JavaScript代码"
                }
            },
            "required": ["script"]
        }
    }
]

async def run_agent(query: str, streaming: bool = True) -> AsyncGenerator[str, None]:
    weather_server = None
    puppeteer_server = None
    try:
        # 初始化天气服务器
        logger.info("初始化天气服务器...")
        weather_server = MCPServerStdio(
            name="weather",
            params={
                "command": "python",
                "args": ["src/mcp/weather.py"],
                "env": {
                    "PYTHONPATH": os.getcwd(),
                    "OPENWEATHER_API_BASE": os.getenv("OPENWEATHER_API_BASE"),
                    "OPENWEATHER_API_KEY": os.getenv("OPENWEATHER_API_KEY")
                }
            },
            cache_tools_list=True
        )
        
        # 初始化Puppeteer服务器（如果需要）
        if USE_PUPPETEER:
            logger.info("初始化Puppeteer服务器...")
            puppeteer_server = MCPServerStdio(
                name="puppeteer",
                params={
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
                    "env": {
                        "PUPPETEER_LAUNCH_OPTIONS": json.dumps(PUPPETEER_LAUNCH_OPTIONS),
                        "ALLOW_DANGEROUS": "true"
                    }
                },
                cache_tools_list=True
            )

            # 搜索并提取信息
            async def search_and_extract(query: str):
                try:
                    # 1. 使用puppeteer_navigate访问搜索引擎
                    await puppeteer_server.call_tool("puppeteer_navigate", {
                        "url": f"https://www.google.com/search?q={query}"
                    })
                    
                    # 2. 使用puppeteer_evaluate提取搜索结果
                    results = await puppeteer_server.call_tool("puppeteer_evaluate", {
                        "script": """
                            return Array.from(document.querySelectorAll('div.g')).map(el => ({
                                title: el.querySelector('h3')?.textContent,
                                link: el.querySelector('a')?.href,
                                snippet: el.querySelector('div.VwiC3b')?.textContent
                            }))
                        """
                    })
                    
                    # 3. 如果需要，可以捕获页面截图
                    await puppeteer_server.call_tool("puppeteer_screenshot", {
                        "name": "search_results",
                        "selector": "div#search"
                    })
                    
                    return results
                except Exception as e:
                    logger.error(f"使用puppeteer工具时出错: {str(e)}")
                    return None

            # 尝试使用puppeteer搜索
            try:
                async with asyncio.timeout(30):  # 设置30秒超时
                    search_results = await search_and_extract(query)
                    if search_results:
                        yield json.dumps({"response": f"搜索到相关信息：{json.dumps(search_results)}"}) + "\n"
            except asyncio.TimeoutError:
                logger.warning("搜索超时")
            except Exception as e:
                logger.error(f"搜索过程中出错: {str(e)}")

        try:
            # 添加超时机制
            async with asyncio.timeout(60):  # 设置60秒超时
                logger.info("正在连接到MCP服务器...")
                # 手动连接到MCP服务器
                await weather_server.connect()
                logger.info("MCP服务器连接成功")

                if USE_PUPPETEER:
                    logger.info("正在连接到Puppeteer服务器...")
                    await puppeteer_server.connect()
                    logger.info("Puppeteer服务器连接成功")

                # 等待服务器连接成功并获取MCP服务可用工具列表
                logger.info("正在获取可用工具列表...")
                tools = await weather_server.list_tools()
                logger.info("可用工具列表:")
                for tool in tools:
                    logger.info(f" - {tool.name}: {tool.description}")

                if USE_PUPPETEER:
                    puppeteer_tools = await puppeteer_server.list_tools()
                    logger.info("Puppeteer工具列表:")
                    for tool in puppeteer_tools:
                        logger.info(f" - {tool.name}: {tool.description}")

                # 创建agent实例
                mcp_servers = [weather_server]
                if USE_PUPPETEER:
                    mcp_servers.append(puppeteer_server)

                weather_agent = Agent(
                    name="生活助手",
                    instructions=(
                        "你是一个专业且全能的生活助手，可以帮助用户查询和分析生活信息。"
                        "你可以使用以下工具来获取信息："
                        "1. 天气查询工具：获取实时天气信息"
                        "2. Puppeteer工具："
                        "   - 使用puppeteer_navigate访问网页"
                        "   - 使用puppeteer_evaluate执行JavaScript代码来提取信息"
                        "   - 使用puppeteer_screenshot捕获重要信息"
                        "请根据用户的问题选择合适的工具组合来获取信息。"
                    ),
                    mcp_servers=mcp_servers,
                    model_settings=ModelSettings(
                        temperature=0.6,
                        top_p=0.9,
                        max_tokens=4096,
                        tool_choice="auto",
                        parallel_tool_calls=True,
                        truncation="auto"
                    )
                )

                logger.info(f"正在处理：{query}")

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

                    logger.info("开始流式响应")
                    try:
                        async for event in result.stream_events():
                            if event.type == "raw_response_event":
                                if isinstance(event.data, ResponseTextDeltaEvent):
                                    yield json.dumps({"response": event.data.delta}) + "\n"
                                elif isinstance(event.data, ResponseContentPartDoneEvent):
                                    yield json.dumps({"response": "\n"}) + "\n"
                            elif event.type == "run_item_stream_event":
                                if event.item.type == "tool_call_item":
                                    logger.info(f"当前被调用工具信息: {event.item}")
                                elif event.item.type == "tool_call_output_item":
                                    logger.info(f"工具调用返回结果: {event.item.output}")
                    except asyncio.TimeoutError:
                        yield json.dumps({"error": "处理超时，请重试。"}) + "\n"
                    except Exception as e:
                        yield json.dumps({"error": f"处理响应时发生错误: {str(e)}"}) + "\n"
                else:
                    logger.info("使用非流式输出模式处理查询...")
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
                        yield json.dumps({"response": result.final_output}) + "\n"
                    else:
                        yield json.dumps({"response": "未获取到信息"}) + "\n"

        except asyncio.TimeoutError:
            yield json.dumps({"error": "连接或处理超时，请重试。"}) + "\n"
        except Exception as e:
            yield json.dumps({"error": f"连接MCP服务或执行查询时出错: {str(e)}"}) + "\n"
            
    except Exception as e:
        yield json.dumps({"error": f"运行天气Agent时出错: {str(e)}"}) + "\n"
    finally:
        # 清理服务器资源
        cleanup_tasks = []
        if weather_server:
            cleanup_tasks.append(weather_server.cleanup())
        if puppeteer_server:
            cleanup_tasks.append(puppeteer_server.cleanup())
        
        if cleanup_tasks:
            try:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
                logger.info("服务器资源清理成功！")
            except Exception as e:
                logger.error(f"清理服务器资源时出错: {e}")

app = Quart(__name__)
app = cors(app, allow_origin="*")  # 允许所有来源的跨域请求

@app.route('/api/weather', methods=['POST'])
async def agent_query():
    """
    接收前端的天气查询请求，并返回结果
    """
    try:
        logger.info("收到新的天气查询请求")
        data = await request.get_json()
        logger.info(f"请求数据: {data}")
        
        query = data.get('query', '')
        streaming = data.get('streaming', True)

        if not query:
            logger.warning("收到空查询请求")
            return jsonify({"error": "查询内容不能为空"}), 400

        async def generate():
            try:
                logger.info("开始生成响应")
                async for chunk in run_agent(query, streaming):
                    yield chunk
            except Exception as e:
                error_msg = f"处理请求时出错: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                yield json.dumps({"error": error_msg}) + "\n"

        logger.info("返回流式响应")
        return Response(generate(), mimetype='text/event-stream')
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500


# 程序入口点
if __name__ == "__main__":
    logger.info("启动服务器...")
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}\n{traceback.format_exc()}")
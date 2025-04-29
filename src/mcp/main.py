from __future__ import annotations
# from flask import Flask, request, jsonify, Response
from quart import Quart, request, jsonify, Response
from quart_cors import cors

import asyncio
import os
import json
import time
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
    set_tracing_disabled,
    function_tool,
)

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

# 获取 playwright 启动选项
USE_PLAYWRIGHT = os.getenv("USE_PLAYWRIGHT", "true").lower() == "true"

try:
    PLAYWRIGHT_LAUNCH_OPTIONS = json.loads(os.getenv("PLAYWRIGHT_LAUNCH_OPTIONS", "{}"))
except json.JSONDecodeError:
    raise ValueError("PLAYWRIGHT_LAUNCH_OPTIONS 格式无效")

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

# 在main.py中添加playwright工具配置
playwright_tools = [
    {
        "name": "playwright_navigate",
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
        "name": "playwright_search",
        "description": "执行搜索并提取结果",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "playwright_screenshot",
        "description": "捕获页面截图",
        "parameters": {
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "要截图的元素选择器"
                },
                "path": {
                    "type": "string",
                    "description": "保存截图的路径"
                }
            },
            "required": ["path"]
        }
    }
]

async def run_teaching_agent(query: str, streaming: bool = True) -> AsyncGenerator[str, None]:
    weather_server = None
    playwright_server = None
    sql_server = None
    
    try:
        # 初始化天气服务器
        logger.info("初始化天气服务器...")
        weather_server = MCPServerStdio(
            name="weather",
            params={
                "command": "python",  # 修改为python而不是C:\\Windows\\System32\\cmd.exe
                "args": ["src/mcp/weather.py"],  # 修复路径格式
                "env": {
                    "PYTHONPATH": os.getcwd()
                }
            },
            cache_tools_list=True
        )
        
        # 初始化SQL服务器
        logger.info("初始化SQL服务器...")
        sql_server = MCPServerStdio(
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

        # 初始化playwrit服务器（如果需要）
        if USE_PLAYWRIGHT:
            logger.info("初始化playwright服务器...")
            playwright_server = MCPServerStdio(
                name="playwright",
                params={
                    "command": "python",
                    "args": ["src/mcp/playwright_server.py"],  # 使用我们创建的服务器脚本
                    "env": {
                        "PYTHONPATH": os.getcwd(),
                        "PLAYWRIGHT_LAUNCH_OPTIONS": json.dumps(PLAYWRIGHT_LAUNCH_OPTIONS)
                    }
                },
                cache_tools_list=True
            )

        try:
            # 增加超时时间到300秒
            async with asyncio.timeout(300):  # 设置300秒超时
                logger.info("正在连接到MCP服务器...")
                # 手动连接到MCP服务器，增加重试机制
                max_retries = 3
                retry_delay = 20
                
                for attempt in range(max_retries):
                    try:
                        await asyncio.wait_for(weather_server.connect(), timeout=30)
                        logger.info("MCP服务器连接成功")
                        break
                    except asyncio.TimeoutError:
                        if attempt == max_retries - 1:
                            logger.error("MCP服务器连接超时，已达到最大重试次数")
                            raise
                        logger.warning(f"MCP服务器连接超时，正在进行第 {attempt + 1} 次重试...")
                        await asyncio.sleep(retry_delay)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            logger.error(f"MCP服务器连接失败: {str(e)}")
                            raise
                        logger.warning(f"MCP服务器连接失败，正在进行第 {attempt + 1} 次重试...")
                        await asyncio.sleep(retry_delay)
                
                for attempt in range(max_retries):
                    try:
                        await asyncio.wait_for(sql_server.connect(), timeout=30)
                        logger.info("SQL服务器连接成功")
                        break
                    except asyncio.TimeoutError:
                        if attempt == max_retries - 1:
                            logger.error("SQL服务器连接超时，已达到最大重试次数")
                            raise
                        logger.warning(f"SQL服务器连接超时，正在进行第 {attempt + 1} 次重试...")
                        await asyncio.sleep(retry_delay)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            logger.error(f"SQL服务器连接失败: {str(e)}")
                            raise
                        logger.warning(f"SQL服务器连接失败，正在进行第 {attempt + 1} 次重试...")
                        await asyncio.sleep(retry_delay)

                if USE_PLAYWRIGHT:
                    for attempt in range(max_retries):
                        try:
                            await asyncio.wait_for(playwright_server.connect(), timeout=30)
                            logger.info("playwright服务器连接成功")
                            break
                        except asyncio.TimeoutError:
                            if attempt == max_retries - 1:
                                logger.error("playwright服务器连接超时，已达到最大重试次数")
                                raise
                            logger.warning(f"playwright服务器连接超时，正在进行第 {attempt + 1} 次重试...")
                            await asyncio.sleep(retry_delay)
                        except Exception as e:
                            if attempt == max_retries - 1:
                                logger.error(f"playwright服务器连接失败: {str(e)}")
                                raise
                            logger.warning(f"playwright服务器连接失败，正在进行第 {attempt + 1} 次重试...")
                            await asyncio.sleep(retry_delay)

                # 等待服务器连接成功并获取MCP服务可用工具列表
                logger.info("正在获取可用工具列表...")
                try:
                    tools = await asyncio.wait_for(weather_server.list_tools(), timeout=30)
                    logger.info("可用工具列表:")
                    for tool in tools:
                        logger.info(f" - {tool.name}: {tool.description}")
                except asyncio.TimeoutError:
                    logger.error("获取工具列表超时")
                    raise
                except Exception as e:
                    logger.error(f"获取工具列表失败: {str(e)}")
                    raise

                if USE_PLAYWRIGHT:
                    try:
                        playwright_tools_list = await asyncio.wait_for(playwright_server.list_tools(), timeout=30)
                        logger.info("playwright工具列表:")
                        for tool in playwright_tools_list:
                            logger.info(f" - {tool.name}: {tool.description}")
                    except asyncio.TimeoutError:
                        logger.error("获取playwright工具列表超时")
                        raise
                    except Exception as e:
                        logger.error(f"获取playwright工具列表失败: {str(e)}")
                        raise
                    # 搜索并提取信息

                    async def _do_search(query: str):
                        """使用 Playwright 执行搜索并提取结果"""
                        try:
                            logger.info(f"开始搜索: {query}")
                            
                            # 1. 导航到搜索引擎
                            await playwright_server.call_tool("playwright_navigate", {
                                "url": "https://www.baidu.com"
                            })
                            
                            # 2. 执行搜索
                            search_results = await playwright_server.call_tool("playwright_search", {
                                "query": query
                            })
                            
                            # 3. 如有必要，捕获截图
                            screenshot_path = f"./screenshots/search_{int(time.time())}.png"
                            os.makedirs("./screenshots", exist_ok=True)
                            
                            await playwright_server.call_tool("playwright_screenshot", {
                                "selector": "#content_left",
                                "path": screenshot_path
                            })
                            
                            logger.info(f"搜索完成，结果: {search_results}")
                            return search_results
                        except Exception as e:
                            logger.error(f"搜索执行失败: {str(e)}")
                            return None

    # 创建agent实例
                mcp_servers = [weather_server, sql_server]
                if USE_PLAYWRIGHT:
                    mcp_servers.append(playwright_server)  # 使用 playwright_server 而不是 playwright_tools

                teaching_agent = Agent(
                    name="教学助手",
                    instructions=(
                        "你是一个专业且全能的生活助手，可以帮助用户查询和分析生活信息。\n"
                        "你可以使用以下工具来获取信息：\n"
                        "1. 天气查询工具：获取实时天气信息\n"
                        "2. SQL查询工具：从数据库中获取信息\n"
                        "3. Playwright工具：\n"
                        "   - 使用playwright_navigate访问网页\n"
                        "   - 使用playwright_search执行搜索并提取结果\n"
                        "   - 使用playwright_screenshot捕获页面截图\n"
                        "请根据用户的问题选择合适的工具组合来获取信息。\n"
                        "请确保回答完整，不要中途停止。\n"
                    ),

                    mcp_servers=mcp_servers,
                    model_settings=ModelSettings(
                        temperature=0.8,
                        top_p=0.95,
                        max_tokens=4096,
                        tool_choice="auto",
                        parallel_tool_calls=True,
                        truncation="auto",
                    )
                )

                logger.info(f"正在处理：{query}")

                if streaming:
                    result = Runner.run_streamed(
                        teaching_agent,
                        input=query,
                        max_turns=10,
                        run_config=RunConfig(
                            model_provider=model_provider,
                            trace_include_sensitive_data=False,
                            handoff_input_filter=None,
                            # timeout=300  # 增加超时时间到300秒
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
                        teaching_agent,
                        input=query,
                        max_turns=10,
                        run_config=RunConfig(
                            model_provider=model_provider,
                            trace_include_sensitive_data=False,
                            handoff_input_filter=None,
                            # timeout=300  # 增加超时时间到300秒
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
        tasks = []
        
        # 创建独立的清理任务
        if weather_server:
            async def cleanup_weather():
                try:
                    await weather_server.cleanup()
                    logger.info("天气服务器资源已清理")
                except Exception as e:
                    logger.error(f"清理天气服务器时出错: {str(e)}")
            tasks.append(asyncio.create_task(cleanup_weather()))
        
        if sql_server:
            async def cleanup_sql():
                try:
                    await sql_server.cleanup()
                    logger.info("SQL服务器资源已清理")
                except Exception as e:
                    logger.error(f"清理SQL服务器时出错: {str(e)}")
            tasks.append(asyncio.create_task(cleanup_sql()))
                
        if playwright_server:
            async def cleanup_playwright():
                try:
                    await playwright_server.cleanup()
                    logger.info("playwright服务器资源已清理")
                except Exception as e:
                    logger.error(f"清理playwright服务器时出错: {str(e)}")
            tasks.append(asyncio.create_task(cleanup_playwright()))
        
        # 等待所有清理任务完成，但不传播异常
        if tasks:
            try:
                # 使用gather并设置return_exceptions=True避免异常传播
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"等待清理任务时发生错误: {str(e)}")
        
        logger.info("所有服务器资源清理完成")

app = Quart(__name__)
app = cors(app, allow_origin="*")  # 允许所有来源的跨域请求

@app.route('/api/query', methods=['POST'])
async def query_agent():
    """
    接收前端的查询请求，调用teaching agent并返回结果
    """
    try:
        logger.info("收到新的查询请求")
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
                async for chunk in run_teaching_agent(query, streaming):
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


@app.route('/api/topics', methods=['POST'])
async def generate_topics():
    """生成学习相关的话题"""
    try:
        # 从请求中获取用户输入（可选）
        logger.info("收到新的话题生成请求")
        data = await request.get_json()
        user_input = data.get("input")
        logger.debug(f"用户输入: {user_input}")

        # 调用OpenAI API生成话题
        try:
            agent = Agent(
                name = "话题生成助手",
                instructions = "你是一个**专业的**学习助手，可以生成一些学习相关的话题。帮助生成**六个**学习相关的话题。话题应涵盖数学、物理、编程等领域，并且每个话题简洁明了，适合大学生学习。**只需要输出话题，不需要解释以及多余的回复。**",
                mcp_servers = [],  # 不使用任何MCP服务器
                model_settings = ModelSettings(
                    temperature = 0.8,
                    top_p = 0.95,
                    max_tokens = 100,
                    tool_choice = "auto",
                    parallel_tool_calls = True,
                    truncation = "auto",
                )
            )
            response = await Runner.run(
                agent,
                input=user_input,
                max_turns=3,
                run_config=RunConfig(
                    model_provider=model_provider,
                    trace_include_sensitive_data=False,
                    handoff_input_filter=None,
                )
            )
        except Exception as e:
            logger.error(f"调用API失败: {str(e)}")
            raise

        # 提取生成的内容
        try:
            topics_text = getattr(response, "final_output", None)
            logger.info(f"原始话题文本: {topics_text}")
            
            # 处理话题文本
            topics = []
            if topics_text:
                # Split by new lines and process each line
                for line in topics_text.split('\n'):
                    # Remove leading/trailing whitespace
                    line = line.strip()
                    # Skip empty lines
                    if not line:
                        continue
                    
                    # Remove numbering (like "1.", "2.") and common list markers
                    clean_line = line
                    for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '0.', '#', '-', '*', '•']:
                        if line.startswith(prefix):
                            clean_line = line[len(prefix):].strip()
                            break
                    
                    # Add the cleaned line to topics if it's not empty
                    if clean_line:
                        topics.append(clean_line)
            
            # 如果没有有效话题，使用默认话题
            if not topics:
                logger.warning("未生成有效话题，使用默认话题")
                topics = [
                    "高等数学中的极限概念如何理解？",
                    "线性代数的特征值和特征向量有什么作用？",
                    "如何解决难度较大的微分方程？",
                    "概率论中的贝叶斯公式应用场景？",
                    "数据结构中哈希表的工作原理是什么？"
                    "C编程语言中的内存管理机制？",
                ]
            
            logger.info(f"生成的话题: {topics}")
            return jsonify({"topics": topics})
        except Exception as e:
            logger.error(f"处理话题文本时出错: {str(e)}")
            raise

    except Exception as e:
        error_msg = f"处理话题生成请求时发生错误: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return jsonify({"error": str(e)}), 500

# 程序入口点
if __name__ == "__main__":
    logger.info("启动服务器...")
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}\n{traceback.format_exc()}")
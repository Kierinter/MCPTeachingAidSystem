from __future__ import annotations
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

# 导入服务器管理函数
from mcp_server_controller import (
    init_and_connect_server,
    cleanup_server,
    cleanup_all_servers,
    get_active_servers,
)

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

# 检查必要的环境变量
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 将日志级别改为INFO
    format='%(message)s'  # 简化日志格式
)
logger = logging.getLogger(__name__)

# 设置其他模块的日志级别
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)


async def run_teaching_agent(query: str, streaming: bool = True) -> AsyncGenerator[str, None]:
    try:
        # 初始化各类服务器

        # await init_and_connect_server("sql")
        await init_and_connect_server("filesystem")
        # await init_and_connect_server("pdf")
        await init_and_connect_server("browser")#考虑 fetch 替换？

        
        # 收集当前活跃的服务器
        active_servers = await get_active_servers()
        
        # 创建agent实例
        teaching_agent = Agent(
            name="教学助手",
            instructions=(
                "你是一个专业且全能的教学助手，可以帮助教师查询知识、总计知识、分析学生信息。\n"
                "请根据用户的问题选择合适的工具组合来获取信息。\n"
                "请确保回答完整，不要中途停止。\n"
                "你可以使用文件系统工具来读取和写入文件。如果没有指定文件夹，则默认读取 'doc' 文件夹\n"
                "你可以使用PDF工具将对话内容或报告导出为PDF文件，特别在用户要求保存或打印对话时。\n"
                "生成PDF时，默认保存到'reports'文件夹，确保先创建该文件夹。\n"
                "牢记之前的对话内容，确保回答时考虑上下文。\n"
                "当涉及数学公式时，请使用标准的 Markdown 数学公式格式：\n"
                "1. 行内公式使用单个美元符号包裹，如：$E=mc^2$\n"
                "2. 行间公式使用两个美元符号包裹，如：$$\\frac{d}{dx}(x^n) = nx^{n-1}$$\n"
                "3. 或使用数学代码块，如：```math\n\\sum_{i=1}^{n} i = \\frac{n(n+1)}{2}\n```\n"
                "请勿使用括号 () 包裹公式，因为这会导致渲染问题。\n"
                "确保 LaTeX 公式中所有特殊字符都正确转义。\n"
            ),
            mcp_servers=active_servers,
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
    finally:
        # 不在每次请求后清理服务器，保持服务器连接以提高性能
        # 清理工作由应用退出时的cleanup函数处理
        logger.info("waiting for next request...")

app = Quart(__name__)
app = cors(app, allow_origin="*")  # 允许所有来源的跨域请求

@app.after_serving
async def cleanup():
    """在服务器关闭时清理资源"""
    await cleanup_all_servers()

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
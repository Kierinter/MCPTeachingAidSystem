import logging
import json
import os
import asyncio
import datetime
from typing import Dict, List, Any, Optional
from fastapi import WebSocket, HTTPException, Depends
from mcp.mcp_server_controller import init_and_connect_server, cleanup_server


class TeachingAI:
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.logger = self.setup_logger()
        self.browser_server = None  # 用于存储浏览器服务的实例

    def setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger("TeachingAI")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def initialize_browser(self):
        """初始化浏览器服务"""
        try:
            self.browser_server = await init_and_connect_server("browser")
            self.logger.info("浏览器服务初始化成功")
            return True
        except Exception as e:
            self.logger.error(f"浏览器服务初始化失败: {str(e)}")
            return False

    async def browse_url(self, url: str) -> Dict[str, Any]:
        """浏览指定的URL"""
        if not self.browser_server:
            success = await self.initialize_browser()
            if not success:
                return {"success": False, "error": "浏览器服务未初始化"}

        try:
            result = await self.browser_server.call_tool("browse", {"url": url})
            return result
        except Exception as e:
            self.logger.error(f"浏览URL失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def cleanup(self):
        """清理资源"""
        try:
            # 清理浏览器服务
            if self.browser_server:
                await cleanup_server("browser")
                self.browser_server = None

            # ...existing code...
        except Exception as e:
            self.logger.error(f"清理资源时出错: {str(e)}")
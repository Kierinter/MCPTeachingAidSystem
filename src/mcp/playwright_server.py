import os
import json
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
import asyncio
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("playwright")

# 全局变量，用于存储 Playwright 实例
browser = None
context = None
page = None
playwright = None

# 读取启动选项
try:
    LAUNCH_OPTIONS = json.loads(os.getenv("PLAYWRIGHT_LAUNCH_OPTIONS", "{}"))
    logger.info(f"Playwright 启动选项: {LAUNCH_OPTIONS}")
except json.JSONDecodeError:
    logger.error("PLAYWRIGHT_LAUNCH_OPTIONS 格式无效")
    LAUNCH_OPTIONS = {}

async def ensure_browser():
    """确保浏览器已经启动，如果没有则启动它"""
    global browser, context, page, playwright
    
    if browser is None:
        try:
            logger.info("正在启动 Playwright 浏览器...")
            playwright = await async_playwright().start()
            
            # 默认使用 chromium
            browser_type = LAUNCH_OPTIONS.pop("browser_type", "chromium")
            if browser_type == "firefox":
                browser = await playwright.firefox.launch(**LAUNCH_OPTIONS)
            elif browser_type == "webkit":
                browser = await playwright.webkit.launch(**LAUNCH_OPTIONS)
            else:
                browser = await playwright.chromium.launch(**LAUNCH_OPTIONS)
            
            logger.info(f"浏览器 {browser_type} 启动成功")
            
            # 创建上下文和页面
            context = await browser.new_context()
            page = await context.new_page()
            logger.info("浏览器页面创建成功")
            
            return True
        except Exception as e:
            logger.error(f"启动浏览器失败: {str(e)}")
            return False
    return True

@mcp.tool("browse", "访问指定的网页")
async def browse(url):
    if not await ensure_browser():
        return {"success": False, "error": "浏览器启动失败"}
    
    try:
        logger.info(f"正在访问网页: {url}")
        await page.goto(url, wait_until="domcontentloaded")
        return {
            "success": True,
            "url": page.url,
            "title": await page.title()
        }
    except Exception as e:
        logger.error(f"访问网页失败: {str(e)}")
        return {"success": False, "error": str(e)}

@mcp.tool("get_content", "获取当前页面的HTML内容")
async def get_content():
    if not await ensure_browser():
        return {"success": False, "error": "浏览器启动失败"}
    
    try:
        content = await page.content()
        return {
            "success": True,
            "content": content
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("screenshot", "截取当前页面的屏幕截图")
async def screenshot(path=None):
    if not await ensure_browser():
        return {"success": False, "error": "浏览器启动失败"}
    
    try:
        if path is None:
            # 生成默认截图路径
            path = f"screenshot_{int(asyncio.get_event_loop().time())}.png"
        
        await page.screenshot(path=path)
        return {
            "success": True,
            "path": path
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("type", "在指定选择器处输入文本")
async def type_text(selector, text):
    if not await ensure_browser():
        return {"success": False, "error": "浏览器启动失败"}
    
    try:
        await page.fill(selector, text)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("click", "点击指定选择器的元素")
async def click(selector):
    if not await ensure_browser():
        return {"success": False, "error": "浏览器启动失败"}
    
    try:
        await page.click(selector)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("extract_text", "提取指定选择器的文本内容")
async def extract_text(selector):
    if not await ensure_browser():
        return {"success": False, "error": "浏览器启动失败"}
    
    try:
        text = await page.text_content(selector)
        return {
            "success": True,
            "text": text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("cleanup", "清理浏览器资源")
async def cleanup():
    global browser, context, page, playwright
    
    try:
        if page:
            await page.close()
            page = None
        
        if context:
            await context.close()
            context = None
        
        if browser:
            await browser.close()
            browser = None
        
        if playwright:
            await playwright.stop()
            playwright = None
        
        return {"success": True, "message": "浏览器资源已清理"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 程序结束时的清理钩子
@mcp.on_shutdown
async def shutdown():
    await cleanup()
    logger.info("Playwright 服务器已关闭")

if __name__ == "__main__":
    mcp.run()
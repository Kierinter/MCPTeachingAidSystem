import os
import json
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
#logger
# import logging

mcp = FastMCP("playwright")

# 全局变量，用于存储 Playwright 实例
browser = None
context = None
page = None

async def ensure_browser():
    """确保浏览器已启动"""
    global browser, context, page
    
    if browser is None:
        # 解析环境变量中的启动选项
        launch_options = {}
        try:
            launch_options_str = os.getenv("PLAYWRIGHT_LAUNCH_OPTIONS", "{}")
            launch_options = json.loads(launch_options_str)
        except json.JSONDecodeError:
            print("警告：PLAYWRIGHT_LAUNCH_OPTIONS 格式无效，使用默认设置")
            launch_options = {"headless": True}
        
        # 启动 Playwright
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(**launch_options)
        context = await browser.new_context()
        page = await context.new_page()
        print("Playwright 浏览器已启动")

@mcp.tool()
async def playwright_navigate(url: str) -> str:
    """导航到指定URL
    
    Args:
        url: 要访问的URL
    
    Returns:
        str: 导航结果
    """
    await ensure_browser()
    try:
        global page
        await page.goto(url, wait_until="domcontentloaded")
        current_url = page.url
        title = await page.title()
        return f"已成功导航到 {current_url}，页面标题: {title}"
    except Exception as e:
        return f"导航到 {url} 时出错: {str(e)}"

@mcp.tool()
async def playwright_search(query: str) -> list:
    """执行搜索并提取结果
    
    Args:
        query: 搜索关键词
    
    Returns:
        list: 搜索结果列表
    """
    await ensure_browser()
    try:
        global page
        
        # 检查当前是否在搜索引擎
        current_url = page.url
        if "baidu.com" in current_url:
            # 百度搜索
            await page.fill("#kw", query)
            await page.click("#su")
            await page.wait_for_load_state("networkidle")
            
            # 提取搜索结果
            results = await page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('.result')).map(el => ({
                        title: el.querySelector('.t')?.textContent?.trim(),
                        link: el.querySelector('a')?.href,
                        snippet: el.querySelector('.c-abstract')?.textContent?.trim()
                    })).filter(item => item.title && item.link);
                }
            """)
            
            return results
        else:
            # 如果不在搜索引擎，先导航到百度
            await playwright_navigate("https://www.baidu.com")
            return await playwright_search(query)
    except Exception as e:
        return f"执行搜索时出错: {str(e)}"

@mcp.tool()
async def playwright_screenshot(path: str, selector: str = None) -> str:
    """捕获页面截图
    
    Args:
        path: 保存截图的路径
        selector: 要截图的元素选择器 (可选)
    
    Returns:
        str: 截图结果
    """
    await ensure_browser()
    try:
        global page
        
        # 确保目录存在
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        if selector:
            # 截取特定元素
            element = await page.wait_for_selector(selector, timeout=5000)
            await element.screenshot(path=path)
        else:
            # 截取整个页面
            await page.screenshot(path=path)
        
        return f"截图已保存到 {path}"
    except Exception as e:
        return f"捕获截图时出错: {str(e)}"

# 清理函数
async def cleanup():
    """清理 Playwright 资源"""
    global browser, context, page
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
        print("Playwright 资源已清理")
    except Exception as e:
        print(f"清理 Playwright 资源时出错: {str(e)}")

# # 程序退出时清理资源
# import atexit
# import asyncio

# def cleanup_handler():
#     loop = asyncio.get_event_loop()
#     if loop.is_running():
#         loop.create_task(cleanup())
#     else:
#         loop.run_until_complete(cleanup())

# atexit.register(cleanup_handler)

# 主程序入口
if __name__ == "__main__":
    print("启动 Playwright MCP 服务...")
    mcp.run(transport='stdio')
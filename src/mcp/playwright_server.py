import os
import json
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
import asyncio

mcp = FastMCP("playwright")

# 全局变量，用于存储 Playwright 实例
browser = None
context = None
page = None
playwright = None

async def ensure_browser():
    """确保浏览器已启动"""
    global browser, context, page, playwright
    
    if browser is None:
        try:
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
        except Exception as e:
            print(f"启动Playwright浏览器时出错: {e}")
            # 直接清理已创建的资源
            if page:
                try:
                    await page.close()
                except:
                    pass
                page = None
            if context:
                try:
                    await context.close()
                except:
                    pass
                context = None
            if browser:
                try:
                    await browser.close()
                except:
                    pass
                browser = None
            if playwright:
                try:
                    await playwright.stop()
                except:
                    pass
                playwright = None
            raise

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
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    await element.screenshot(path=path)
                else:
                    await page.screenshot(path=path)
                    return f"找不到选择器 '{selector}'，已截取整个页面: {path}"
            except Exception as e:
                await page.screenshot(path=path)
                return f"截取元素时出错: {str(e)}，已截取整个页面: {path}"
        else:
            # 截取整个页面
            await page.screenshot(path=path)
        
        return f"截图已保存到 {path}"
    except Exception as e:
        return f"捕获截图时出错: {str(e)}"

# 清理函数
async def cleanup():
    """清理 Playwright 资源"""
    global browser, context, page, playwright
    
    # 逐个清理资源，每个步骤都使用独立的try-except块
    if page:
        try:
            await page.close()
            print("已关闭页面")
        except Exception as e:
            print(f"关闭页面时出错: {str(e)}")
        finally:
            page = None
            
    if context:
        try:
            await context.close()
            print("已关闭上下文")
        except Exception as e:
            print(f"关闭上下文时出错: {str(e)}")
        finally:
            context = None
            
    if browser:
        try:
            await browser.close()
            print("已关闭浏览器")
        except Exception as e:
            print(f"关闭浏览器时出错: {str(e)}")
        finally:
            browser = None
            
    if playwright:
        try:
            await playwright.stop()
            print("已停止Playwright")
        except Exception as e:
            print(f"停止Playwright时出错: {str(e)}")
        finally:
            playwright = None
            
    print("Playwright 资源已清理")

# Playwright 资源由 FastMCP 生命周期管理
@mcp.on_shutdown
async def shutdown_handler():
    """在 MCP 服务器关闭时清理 Playwright 资源"""
    await cleanup()

# 主程序入口
if __name__ == "__main__":
    print("启动 Playwright MCP 服务...")
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        print(f"MCP服务器运行出错: {str(e)}")
    finally:
        # 确保在程序退出时清理资源
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(cleanup())
        else:
            loop.run_until_complete(cleanup())
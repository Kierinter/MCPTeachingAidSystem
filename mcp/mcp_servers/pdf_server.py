from mcp.server.fastmcp import FastMCP
import os
import sys
import logging
import traceback
import tempfile
import subprocess
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("pdf-mcp")

# 确保report目录存在
REPORT_DIR = os.path.abspath("reports")
os.makedirs(REPORT_DIR, exist_ok=True)
logger.info(f"PDF输出目录: {REPORT_DIR}")

try:
    mcp = FastMCP("pdf")
    logger.info("FastMCP PDF服务器初始化成功")
except Exception as e:
    logger.error(f"FastMCP 初始化失败: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

@mcp.tool()
async def markdown_to_pdf(content: str, output_filename: str = None, title: str = None) -> dict:
    """将Markdown内容转换为PDF文件
    
    Args:
        content: Markdown格式的内容
        output_filename: 输出的PDF文件名（可选，不含路径和扩展名）
        title: PDF文档标题（可选）
    
    Returns:
        dict: 包含PDF文件路径或错误信息
    """
    try:
        # 如果未指定输出文件名，使用当前时间戳
        if not output_filename:
            import time
            output_filename = f"report_{int(time.time())}"

        # 确保文件名不包含路径和扩展名
        output_filename = os.path.basename(output_filename)
        output_filename = output_filename.replace(".pdf", "")

        # 设置PDF标题
        if not title:
            title = output_filename

        # 创建完整的输出路径
        output_path = os.path.join(REPORT_DIR, f"{output_filename}.pdf")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        logger.info(f"准备将Markdown内容转换为PDF: {output_path}")

        # 创建临时Markdown文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as temp_file:
            temp_path = temp_file.name
            temp_file.write(content)

        try:
            # 检查是否安装了pandoc
            try:
                subprocess.run(['pandoc', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            except (subprocess.SubprocessError, FileNotFoundError):
                return {"error": "未找到Pandoc，请安装Pandoc以支持PDF生成"}

            # 使用pandoc将Markdown转换为PDF
            cmd = [
                'pandoc',
                temp_path,
                '-o', output_path,
                '--pdf-engine=xelatex',
                '-V', f'title={title}',
                '-V', 'geometry:margin=1in',
                '-V', 'mainfont=SimSun',  # 中文支持
                '-V', 'monofont=Courier New',
                '--standalone'
            ]
            
            logger.info(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            
            if os.path.exists(output_path):
                logger.info(f"PDF生成成功: {output_path}")
                return {
                    "success": True,
                    "message": f"PDF生成成功",
                    "file_path": output_path
                }
            else:
                logger.error("PDF生成失败，输出文件不存在")
                return {"error": "PDF生成失败，输出文件不存在", "stderr": result.stderr.decode('utf-8', errors='replace')}
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Pandoc执行失败: {e}")
            stderr = e.stderr.decode('utf-8', errors='replace')
            logger.error(f"Pandoc错误输出: {stderr}")
            return {"error": f"PDF生成失败: {stderr}"}
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"生成PDF时出错: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}

@mcp.tool()
async def get_pdf_info() -> dict:
    """获取PDF生成服务的状态信息
    
    Returns:
        dict: PDF服务的状态信息
    """
    try:
        return {
            "status": "active",
            "output_directory": REPORT_DIR,
            "has_pandoc": _check_pandoc_installed()
        }
    except Exception as e:
        logger.error(f"获取PDF服务信息时出错: {str(e)}")
        return {"error": str(e)}

def _check_pandoc_installed() -> bool:
    """检查是否安装了pandoc"""
    try:
        subprocess.run(['pandoc', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

@mcp.tool()
async def html_to_pdf(html_content: str, output_filename: str = None, title: str = None) -> dict:
    """将HTML内容转换为PDF文件
    
    Args:
        html_content: HTML格式的内容
        output_filename: 输出的PDF文件名（可选，不含路径和扩展名）
        title: PDF文档标题（可选）
    
    Returns:
        dict: 包含PDF文件路径或错误信息
    """
    try:
        # 如果未指定输出文件名，使用当前时间戳
        if not output_filename:
            import time
            output_filename = f"report_{int(time.time())}"

        # 确保文件名不包含路径和扩展名
        output_filename = os.path.basename(output_filename)
        output_filename = output_filename.replace(".pdf", "")

        # 创建完整的输出路径
        output_path = os.path.join(REPORT_DIR, f"{output_filename}.pdf")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 创建临时HTML文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_file:
            temp_path = temp_file.name
            temp_file.write(html_content)
        
        try:
            # 检查是否安装了wkhtmltopdf或pandoc
            if _check_wkhtmltopdf_installed():
                cmd = [
                    'wkhtmltopdf',
                    '--encoding', 'utf-8',
                    temp_path,
                    output_path
                ]
                logger.info(f"使用wkhtmltopdf转换HTML到PDF")
            elif _check_pandoc_installed():
                cmd = [
                    'pandoc',
                    temp_path,
                    '-o', output_path,
                    '--pdf-engine=xelatex',
                    '-V', 'geometry:margin=1in',
                    '-V', 'mainfont=SimSun',  # 中文支持
                ]
                logger.info(f"使用pandoc转换HTML到PDF")
            else:
                return {"error": "未找到wkhtmltopdf或pandoc，无法生成PDF"}
            
            logger.info(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            
            if os.path.exists(output_path):
                logger.info(f"PDF生成成功: {output_path}")
                return {
                    "success": True,
                    "message": f"PDF生成成功",
                    "file_path": output_path
                }
            else:
                logger.error("PDF生成失败，输出文件不存在")
                return {"error": "PDF生成失败，输出文件不存在"}
        except subprocess.CalledProcessError as e:
            logger.error(f"转换工具执行失败: {e}")
            stderr = e.stderr.decode('utf-8', errors='replace')
            logger.error(f"错误输出: {stderr}")
            return {"error": f"PDF生成失败: {stderr}"}
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_path)
            except:
                pass
    except Exception as e:
        logger.error(f"生成PDF时出错: {str(e)}")
        traceback.print_exc()
        return {"error": str(e)}

def _check_wkhtmltopdf_installed() -> bool:
    """检查是否安装了wkhtmltopdf"""
    try:
        subprocess.run(['wkhtmltopdf', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

# 主程序入口
if __name__ == "__main__":
    try:
        logger.info("启动PDF生成MCP服务...")
        mcp.run(transport='stdio')
    except KeyboardInterrupt:
        logger.info("PDF生成MCP服务已被用户中断")
    except Exception as e:
        logger.error(f"运行PDF生成MCP服务时发生错误: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
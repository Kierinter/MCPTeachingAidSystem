import asyncio
import os
import logging
import sys
import time
import json
import requests
from typing import Dict, Any, List, Optional

from agents.mcp import MCPServiceBase
from agents.mcp.tools import get_open_api_schemas

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("weather_service")

class WeatherService(MCPServiceBase):
    """天气服务，提供天气查询功能"""

    def __init__(self):
        super().__init__()
        self.register_tool("get_weather", self.get_weather_by_city)
        self.register_tool("get_weather_forecast", self.get_weather_forecast)
        logger.info("天气服务初始化完成")

    async def get_weather_by_city(self, city: str) -> Dict[str, Any]:
        """
        获取指定城市的当前天气
        
        参数:
            city: 城市名称，如"北京"、"上海"等
            
        返回:
            包含天气信息的字典
        """
        try:
            logger.info(f"正在查询城市 {city} 的天气")
            
            # 使用高德地图API获取天气数据
            # API文档：https://lbs.amap.com/api/webservice/guide/api/weatherinfo/
            api_key = os.getenv("AMAP_KEY")  # 使用环境变量或默认值
            
            # 构建API请求URL
            url = f"https://restapi.amap.com/v3/weather/weatherInfo?key={api_key}&city={city}&extensions=base"
            
            logger.info(f"发送请求: {url}")
            response = requests.get(url, timeout=10)
            logger.info(f"收到响应码: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"API请求失败: {response.text}")
                return {
                    "error": f"获取天气失败，状态码: {response.status_code}",
                    "city": city
                }
            
            data = response.json()
            logger.info(f"API返回数据: {data}")
            
            # 检查API响应状态
            if data.get("status") != "1":
                logger.error(f"API响应错误: {data.get('info')}")
                return {
                    "error": f"获取天气失败: {data.get('info')}",
                    "city": city
                }
            
            # 检查是否返回了天气数据
            lives = data.get("lives", [])
            if not lives:
                logger.warning(f"未找到城市 {city} 的天气数据")
                return {
                    "error": f"未找到城市 {city} 的天气数据",
                    "city": city
                }
            
            # 提取天气数据
            weather_data = lives[0]
            
            return {
                "city": weather_data.get("city", city),
                "weather": weather_data.get("weather", "未知"),
                "temperature": weather_data.get("temperature", "未知"),
                "wind_direction": weather_data.get("winddirection", "未知"),
                "wind_power": weather_data.get("windpower", "未知"),
                "humidity": weather_data.get("humidity", "未知"),
                "report_time": weather_data.get("reporttime", "未知")
            }
            
        except Exception as e:
            logger.error(f"获取天气时出错: {str(e)}", exc_info=True)
            return {
                "error": f"获取天气时出错: {str(e)}",
                "city": city
            }

    async def get_weather_forecast(self, city: str) -> Dict[str, Any]:
        """
        获取指定城市的天气预报(未来3天)
        
        参数:
            city: 城市名称，如"北京"、"上海"等
            
        返回:
            包含天气预报信息的字典
        """
        try:
            logger.info(f"正在查询城市 {city} 的天气预报")
            
            # 使用高德地图API获取天气预报数据
            api_key = os.getenv("AMAP_KEY", "4320a258c4832dca748b113d3d3befa1")
            
            # 构建API请求URL - 使用forecast参数获取预报
            url = f"https://restapi.amap.com/v3/weather/weatherInfo?key={api_key}&city={city}&extensions=all"
            
            logger.info(f"发送预报请求: {url}")
            response = requests.get(url, timeout=10)
            logger.info(f"收到预报响应码: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"预报API请求失败: {response.text}")
                return {
                    "error": f"获取天气预报失败，状态码: {response.status_code}",
                    "city": city
                }
            
            data = response.json()
            logger.info(f"预报API返回数据: {data}")
            
            # 检查API响应状态
            if data.get("status") != "1":
                logger.error(f"预报API响应错误: {data.get('info')}")
                return {
                    "error": f"获取天气预报失败: {data.get('info')}",
                    "city": city
                }
            
            # 检查是否返回了预报数据
            forecasts = data.get("forecasts", [])
            if not forecasts:
                logger.warning(f"未找到城市 {city} 的天气预报数据")
                return {
                    "error": f"未找到城市 {city} 的天气预报数据",
                    "city": city
                }
            
            # 提取城市和预报列表
            forecast_data = forecasts[0]
            city_name = forecast_data.get("city", city)
            casts = forecast_data.get("casts", [])
            
            # 格式化预报数据
            forecast_list = []
            for cast in casts:
                forecast_list.append({
                    "date": cast.get("date", "未知"),
                    "day_weather": cast.get("dayweather", "未知"),
                    "night_weather": cast.get("nightweather", "未知"),
                    "day_temp": cast.get("daytemp", "未知"),
                    "night_temp": cast.get("nighttemp", "未知"),
                    "day_wind": cast.get("daywind", "未知"),
                    "night_wind": cast.get("nightwind", "未知"),
                    "day_power": cast.get("daypower", "未知"),
                    "night_power": cast.get("nightpower", "未知")
                })
            
            return {
                "city": city_name,
                "forecast": forecast_list,
                "report_time": forecast_data.get("reporttime", "未知")
            }
            
        except Exception as e:
            logger.error(f"获取天气预报时出错: {str(e)}", exc_info=True)
            return {
                "error": f"获取天气预报时出错: {str(e)}",
                "city": city
            }
    
    async def get_tools_list(self) -> List[Dict[str, Any]]:
        tools = get_open_api_schemas(
            {
                "get_weather": self.get_weather_by_city,
                "get_weather_forecast": self.get_weather_forecast
            }
        )
        return tools

async def main():
    # 创建天气服务实例
    service = WeatherService()
    
    # 启动服务
    try:
        logger.info("正在启动天气服务...")
        await service.run()
    except Exception as e:
        logger.error(f"天气服务运行时出错: {str(e)}", exc_info=True)
    finally:
        logger.info("天气服务已关闭")

if __name__ == "__main__":
    asyncio.run(main())
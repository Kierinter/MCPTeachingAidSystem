# 基于MCP的内置智能体的AI教辅系统
这是一个基于MCP (Machine Conversation Protocol) 的智能教学辅助系统，融合了大模型能力与智能代理技术，为教师提供课堂助力。

## 项目概述

本系统基于MCP协议和大语言模型，打造了一个智能化的教学辅助工具，可帮助教师进行知识查询、课程规划、学生辅导和资料整理等工作。通过对话式交互方式，为教育工作者提供智能化教学支持。

## 技术栈

- **前端**：Vue 3 + Tailwind CSS + Element Plus
- **大模型提供商**：Deepseek V3
- **Agent实现**：OpenAI Agent API，MCP Python API
- **服务端**：Quart + CORS
- **数据存储**：MySQL
- **浏览器交互**：Puppeteer

## 功能特点

- **智能对话辅导**：AI助手可回答各种学术问题，提供清晰的解释和引导
- **个性化学习路径**：系统分析学习情况，推荐适合的学习内容和进度
- **实时反馈评估**：练习后获得即时反馈，了解掌握程度和需改进的地方
- **多媒体学习资源**：提供视频、图表和互动内容，满足不同学习风格的需求
- **文档生成导出**：支持PDF文件生成，便于保存和分享学习内容
- **网页信息检索**：通过浏览器服务获取在线资源和信息

## 集成MCP服务

系统集成了以下MCP服务器:

- **SQL MCP**: 提供数据库查询能力，用于存取学生信息和学习数据
- **Browser MCP**: 支持网页交互和信息检索，可访问在线教育资源
- **Filesystem MCP**: 提供文件读写功能，管理教案和学习材料
- **PDF MCP**: 支持将对话内容和学习报告导出为PDF文件

## 启动方式

### 环境要求

- Python 3.13+
- Node.js 18+

### 后端设置

1. 安装Python依赖:

```bash
uv venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
uv pip install -e .
```

2. 配置环境变量:
   项目已包含基本的`.env`文件，如需修改可调整`mcp/.env`中的设置。

3. 启动MCP服务:

```bash
cd mcp
python main.py
```

4. 启动后端服务:

```bash

python run_server.py
```

### 前端设置

1. 安装Node.js依赖:

```bash
npm install
```

2. 启动开发服务器:

```bash
npm run dev
```

3. 构建生产版本:

```bash
npm run build
```

## 项目结构

- **src/components**: Vue组件，包含对话界面、登录页等
- **/mcp**: MCP服务器实现
  - main.py: 核心服务器和Agent集成
  - pdf_server.py: PDF生成服务
  - filesystem-server.py: 文件管理服务
  - browser-server.py: 网页浏览服务
  - local_web_server.py: 本地网页跳转服务
- **src/router**: 前端路由配置
- **src/agents**: Agent实现和控制逻辑
- **src/assets**: 静态资源
- **doc**: 教案和教学资料

## 测试与调试

系统提供了测试工具来验证各模块功能:

- `test_agent_connection.py`: 测试与Agent的连接
- `test_mysql.py`: 验证数据库连接

### 题库生成与导入

题库生成和导入功能可以通过`题库生成器`模块实现。用户可以根据需要生成不同类型的题目，并将其导入到系统中进行使用。


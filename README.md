# 基于MCP的内置智能体的AI教辅系统
这是一个基于MCP (Machine Conversation Protocol) 的智能教学辅助系统，融合了大模型能力与智能代理技术，为教师提供课堂助力。




## 技术栈

- **前端**：Vue 3 + Tailwind CSS
- **大模型提供商**：Deepseek V3
- **Agent实现**：OpenAI Agent API，MCP Python API

## 功能特点

- **智能对话辅导**：AI助手可回答各种学术问题，提供清晰的解释和引导
- **个性化学习路径**：系统分析学习情况，推荐适合的学习内容和进度
- **实时反馈评估**：练习后获得即时反馈，了解掌握程度和需改进的地方
- **多媒体学习资源**：提供视频、图表和互动内容，满足不同学习风格的需求

## 集成MCP服务

系统集成了以下MCP服务器:

- **Weather MCP**: 提供天气信息查询功能
- **Playwright MCP**: 支持网页交互和信息检索
- **SQL MCP**: 提供数据库查询能力

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
   项目已包含基本的`.env`文件，如需修改可调整`src/mcp/.env`中的设置。

3. 启动后端服务:

```bash
cd src/mcp
python main.py
```

### 前端设置

1. 安装Node.js依赖:

2. 启动开发服务器:

3. 构建生产版本:


```bash
npm install
npm run dev
npm run build
```

## 项目结构

- components: Vue组件
- mcp: MCP服务器实现
  - main.py: 核心服务器
  - weather.py: 天气MCP服务
  - playwright_server.py: 网页交互服务
- router: 前端路由
- assets: 静态资源

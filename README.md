# 交互式数据分析平台

## 项目简介
本平台结合大语言模型与可视化技术，提供自然语言驱动的交互式数据分析体验。支持数据上传、智能分析、可视化生成、分析报告生成等功能。

## 功能特性
- 自然语言交互式数据分析
- 自动化分析方案生成
- 交互式可视化图表生成
- 多步骤分析流程支持
- 分析结果Markdown报告导出

## 技术栈
### 后端
- Python 3.10+
- FastAPI (REST API)
- Pandas/Numpy (数据处理)
- Plotly/Dash (可视化生成)
- LangChain (大模型集成)

### 前端
- React 18
- React Markdown
- React Bootstrap
- Plotly.js

## 快速开始
### 环境要求
- Node.js 18+
- Python 3.10+

### 后端安装
```bash
pip install -r requirements.txt
```

### 前端安装
```bash
cd frontend
npm install
```

### 运行系统
启动后端服务：
```bash
uvicorn app.main:app --reload
```

启动前端应用：
```bash
cd frontend
npm start
```

## 项目结构
```
├── app/            # 后端核心逻辑
├── config/         # 配置文件
├── data/           # 数据集存储
├── frontend/       # 前端React应用
├── static/         # 文件上传目录
├── tests/          # 单元测试
└── requirements.txt
```

## 贡献指南
1. Fork仓库并创建特性分支
2. 提交清晰的commit信息
3. 编写单元测试
4. 创建Pull Request

---

# Interactive Data Analysis Platform

## Project Overview
An AI-powered platform for natural language driven data analysis with automated insights generation and interactive visualization capabilities.

## Key Features
- NLP-driven data analysis
- Automated analysis plan generation
- Interactive visualization builder
- Multi-step analysis workflow
- Markdown report export

## Tech Stack
### Backend
- Python 3.10+
- FastAPI
- Pandas/Numpy
- Plotly/Dash
- LangChain

### Frontend
- React 18
- React Markdown
- React Bootstrap
- Plotly.js

## Development Setup
### Prerequisites
- Node.js 18+
- Python 3.10+

### Backend Setup
```bash
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Running the System
Start backend:
```bash
uvicorn app.main:app --reload
```

Start frontend:
```bash
cd frontend
npm start
```

## License
MIT
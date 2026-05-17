# Agent Orchestra

一个基于 CrewAI 和 LangChain 的多智能体协作系统，使用 Streamlit 构建交互界面。

## 快速开始

### 1. 克隆或进入项目目录

```bash
cd agent-orchestra
```

### 2. 创建虚拟环境

```bash
python -m venv .venv
```

### 3. 激活虚拟环境

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 4. 安装依赖

使用 uv（推荐，速度更快）：
```bash
pip install uv
uv pip install crewai langchain streamlit python-dotenv
```

或使用 pip：
```bash
pip install crewai langchain streamlit python-dotenv
```

或使用 requirements.txt：
```bash
pip install -r requirements.txt
```

### 5. 配置环境变量

复制示例环境文件并填入你的 API 密钥：
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的 API 密钥
```

### 6. 运行项目

运行 Streamlit 应用：
```bash
streamlit run app.py
```

运行多智能体协作示例：
```bash
python main.py
```

## 项目结构

```
agent-orchestra/
├── .venv/               # 虚拟环境
├── .env                 # 环境变量（需自行创建）
├── .env.example         # 环境变量示例
├── .gitignore           # Git 忽略文件
├── app.py               # Streamlit 应用入口
├── main.py              # 多智能体协作示例
├── test_import.py       # 环境验证脚本
├── agents/              # 智能体定义
│   └── example_agent.py # 示例智能体
├── tasks/               # 任务定义
│   └── example_task.py  # 示例任务
├── tools/               # 工具定义
│   └── example_tool.py  # 示例工具
├── requirements.txt     # Python 依赖
└── README.md            # 项目说明
```

## 核心依赖

- **crewai**: 多智能体协作框架
- **langchain**: LLM 应用开发框架
- **streamlit**: Web 应用界面
- **python-dotenv**: 环境变量管理

## 环境变量

在 `.env` 文件中配置以下变量：

```env
OPENAI_API_KEY=your_openai_api_key_here
# 其他 API 密钥...
```

## 开发

安装开发依赖：
```bash
uv pip install pytest black flake8
```

验证环境：
```bash
python test_import.py
```

运行测试：
```bash
pytest
```

格式化代码：
```bash
black .
```

## 许可证

MIT License
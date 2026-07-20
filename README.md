# NeuroSync ♟️

**博弈论多智能体决策助手** — 让你的问题获得最严厉的博弈论剖析。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

> **三个 AI 博弈论专家，顺序协作，帮你分析现实困境。**  
> 不是鸡汤，是策略。不是直觉，是均衡。

## 架构

```
用户情境 → [博弈建模师] → 结构化模型 → [均衡分析师] → 均衡结果 → [策略顾问] → 行动建议
```

| Agent | 角色 | 职责 |
|-------|------|------|
| **博弈建模师** | Game Modeler | 将现实情境转化为规范的博弈论模型 |
| **均衡分析师** | Equilibrium Analyst | 计算 Nash 均衡、占优策略、Pareto 前沿 |
| **策略顾问** | Strategy Advisor | 基于分析给出可执行的策略建议 |

## 快速开始

1. **克隆仓库**
   ```bash
   git clone <repo-url>
   cd NeuroSync
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的 API Key
   ```

4. **运行 CLI**
   ```bash
   python main.py "我的同事总是抢功劳，我该怎么办？"
   python main.py --preset pricing
   ```

5. **运行 Web 界面**
   ```bash
   streamlit run app.py
   ```

## 预设场景

- **职场博弈** — 办公室政治与晋升竞争
- **定价竞争** — 商家定价策略分析
- **谈判策略** — 薪资谈判与商务谈判
- **情侣关系** — 协调博弈与性别战

## 计算工具

| 工具 | 类型 | 功能 |
|------|------|------|
| `build_payoff_matrix` | 验证工具 | 标准化收益矩阵格式 |
| `identify_game_type` | 规则引擎 | 识别囚徒困境/斗鸡/猎鹿等经典博弈 |
| `solve_pure_nash` | 算法 | 暴力搜索纯策略 Nash 均衡 |
| `solve_mixed_nash` | 代数公式 | 求解 2×2 混合策略均衡 |
| `check_dominance` | 算法 | 识别占优/劣策略 |
| `pareto_analysis` | 算法 | 计算 Pareto 前沿面 |

## 技术栈

- **CrewAI** — 多智能体编排框架
- **Streamlit** — 前端界面
- **LiteLLM** — 模型路由（支持 OpenAI / DeepSeek / Ollama 等）
- **Pydantic** — 工具输入验证

## 参考理论

本系统的博弈论框架参考《策略博弈》(Games of Strategy) — Avinash Dixit & Susan Skeath，涵盖：

- 完全/不完全信息博弈
- 同时/顺序行动博弈
- 重复博弈与声誉机制
- 行为博弈论
- 承诺、信号与策略行动

## License

MIT

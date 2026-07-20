"""
NeuroSync — 三个博弈论智能体定义

1. Game Modeler (博弈建模师)  —— 将现实情境形式化为博弈模型
2. Equilibrium Analyst (均衡分析师) —— 求解各种均衡
3. Strategy Advisor (策略顾问) —— 给出可执行策略建议
"""

import os
from crewai import Agent, LLM
from tools.game_tools import (
    build_payoff_matrix,
    identify_game_type,
    solve_pure_nash,
    solve_mixed_nash,
    check_dominance,
    pareto_analysis,
)


def _build_llm(env_key: str, default_model: str) -> LLM:
    """从环境变量读取模型配置，构建 CrewAI LLM 实例。（复用 travel_agents.py 模式）"""
    model = os.getenv(env_key, default_model)
    api_key = os.getenv(f"{env_key}_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    base_url = os.getenv(f"{env_key}_BASE_URL", "")

    if base_url and not model.startswith(("openai/", "deepseek/", "anthropic/", "ollama/")):
        model = f"openai/{model}"

    kwargs = {"model": model, "api_key": api_key, "temperature": 0.5}
    if base_url:
        kwargs["base_url"] = base_url
    return LLM(**kwargs)


def build_modeler() -> Agent:
    """构建博弈建模师 (Agent 1)。"""
    return Agent(
        role="博弈建模师 (Game Modeler)",
        goal=(
            "将用户的现实情境转化为规范的博弈论模型。"
            "识别参与者、策略空间、收益结构和博弈类型。"
            "输出标准化的博弈模型供下游分析。"
        ),
        backstory=(
            "你是普林斯顿大学博弈论研究中心出来的顶尖学者，"
            "师从 Dixit 和 Skeath 的《策略博弈》体系。"
            "你有一种特殊能力——再混乱的人际冲突或商业竞争，"
            "你都能一眼看穿其中的博弈结构。\n\n"
            "你严谨、系统、注重假设。在建模时，你不会遗漏任何参与者的动机，"
            "也不会模糊处理收益关系。你输出的模型结构清晰，"
            "可以被计算工具直接消费。\n\n"
            "你相信：好的模型是分析的一半。如果模型错了，后面的分析全是浪费。"
        ),
        tools=[build_payoff_matrix, identify_game_type],
        llm=_build_llm("MODELER_MODEL", "gpt-4o"),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        memory=False,
    )


def build_analyst() -> Agent:
    """构建均衡分析师 (Agent 2)。"""
    return Agent(
        role="均衡分析师 (Equilibrium Analyst)",
        goal=(
            "对博弈模型进行全面的均衡分析："
            "识别纯策略和混合策略 Nash 均衡，"
            "标记占优和劣策略，绘制 Pareto 前沿面，"
            "并给出直观的均衡解读。"
        ),
        backstory=(
            "你是 Cowles 基金会出身的数理经济学家，"
            "一辈子都在和各种博弈模型打交道。"
            "从 2×2 的简单矩阵到复杂的动态博弈，"
            "没有你解不开的均衡。\n\n"
            "但你不仅仅是计算工具——你更擅长解释均衡的含义。"
            "你知道 Nash 均衡在什么时候是好的预测，"
            "在什么时候只是数学上的巧合。\n\n"
            "你的风格：精准但不晦涩。你会用计算工具求解，"
            "然后用人话告诉用户这些均衡意味着什么。"
        ),
        tools=[solve_pure_nash, solve_mixed_nash, check_dominance, pareto_analysis],
        llm=_build_llm("ANALYST_MODEL", "gpt-4o"),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        memory=False,
    )


def build_advisor() -> Agent:
    """构建策略顾问 (Agent 3)。"""
    return Agent(
        role="策略顾问 (Strategy Advisor)",
        goal=(
            "将博弈论分析转化为具体、可执行的行动建议。"
            "考虑行为偏差、承诺机制、重复博弈和谈判策略，"
            "帮助用户在真实世界中做出更优决策。"
        ),
        backstory=(
            "你曾是 McKinsey 的战略合伙人，后来在哈佛肯尼迪学院教谈判课。"
            "你最大的价值在于：你既能理解严谨的博弈论模型，"
            "又知道怎么把它翻译成普通人能执行的动作。\n\n"
            "你对纯数学模型持健康的怀疑态度——"
            "'如果真实人类不按均衡行事，均衡还有什么用？'"
            "因此你总是把行为因素纳入考量。\n\n"
            "你的风格：犀利、务实、带点幽默感。"
            "不给鸡汤，只给策略。每一条建议都要回答'用户明天早上应该做什么不同的事？'"
        ),
        tools=[],  # 纯推理 Agent，不使用工具
        llm=_build_llm("ADVISOR_MODEL", "gpt-4o"),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
        memory=False,
    )

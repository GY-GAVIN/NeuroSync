"""
Travel Genius 双 Agent 配置
- Inspiration Explorer：灵感探索者，负责生成旅行推荐
- Savvy Decision Maker：精明决策者，负责筛选和点评
"""

import os
from crewai import Agent, LLM
from tools.travel_tools import search_places, check_practicality


def _build_llm(env_key: str, default_model: str) -> LLM:
    """从环境变量读取模型配置，构建 CrewAI LLM 实例"""
    model = os.getenv(env_key, default_model)
    api_key = os.getenv(f"{env_key}_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    base_url = os.getenv(f"{env_key}_BASE_URL", "")

    # 自定义 base_url 时，加 openai/ 前缀让 LiteLLM 走 OpenAI 兼容协议
    if base_url and not model.startswith(("openai/", "deepseek/", "anthropic/", "ollama/")):
        model = f"openai/{model}"

    kwargs = {"model": model, "api_key": api_key, "temperature": 0.7}
    if base_url:
        kwargs["base_url"] = base_url
    return LLM(**kwargs)


def build_explorer() -> Agent:
    """构建灵感探索者 Agent（Agent A）"""
    return Agent(
        role="灵感探索者 (Inspiration Explorer)",
        goal=(
            "根据用户的旅行需求和兴趣，生成一份包含至少 5 个选项的原始推荐列表。"
            "每个选项必须包含：地点名称、类型、简短推荐理由。"
            "力求新鲜、有趣、超越常规攻略的推荐。"
        ),
        backstory=(
            "你是一个走遍世界的旅行博主，网名'路痴但到得了'。"
            "你对隐藏的小众景点和潮流艺术圣地了如指掌，"
            "朋友们出行前都会来问你，而你从未让人失望过。"
            "你的风格是热情洋溢、充满想象力，总能发现别人忽略的美好。"
            "输出时用列表格式，每个选项附上一句话推荐理由。"
        ),
        tools=[search_places],
        llm=_build_llm("EXPLORER_MODEL", "gpt-4o-mini"),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )


def build_decision_maker() -> Agent:
    """构建精明决策者 Agent（Agent B）"""
    return Agent(
        role="精明决策者 (Savvy Decision Maker)",
        goal=(
            "从灵感探索者给出的推荐列表中，根据用户的预算、时间、口味等约束条件，"
            "精选出最合适的 2-3 个选项，并给出犀利、有用、带幽默感的点评。"
            "每个通过筛选的选项必须说明为什么值得去，以及一个实用小贴士。"
        ),
        backstory=(
            "你在东京生活了十年，网名'东京毒舌导游'。"
            "你对哪里排队、哪里踩雷、哪里物超所值一清二楚。"
            "你说话风格带点毒舌，但建议总是中肯的。"
            "你最讨厌那种'网红打卡但其实很无聊'的地方，"
            "你推荐的地方一定是自己会反复去的。"
            "你的点评格式：一句话毒舌评价 + 为什么值得去 + 一个实用贴士。"
        ),
        tools=[check_practicality],
        llm=_build_llm("DECISION_MODEL", "gpt-4o"),
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )

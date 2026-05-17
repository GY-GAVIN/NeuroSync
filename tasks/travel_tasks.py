"""
Travel Genius 任务定义
定义两个协作任务：灵感搜索 → 可行性筛选
"""

from crewai import Task, Agent


def create_inspiration_task(explorer: Agent, user_input: str) -> Task:
    """
    任务 1：灵感探索
    Agent A 根据用户输入生成原始推荐列表
    """
    return Task(
        description=(
            f"用户需求：{user_input}\n\n"
            "你的任务：\n"
            "1. 使用 search_places 工具，根据用户的兴趣关键词搜索地点\n"
            "2. 在工具返回结果的基础上，结合你的旅行经验，补充推荐理由\n"
            "3. 最终输出一份包含 5-8 个选项的推荐列表\n"
            "4. 每个选项格式：\n"
            "   - 地点名称\n"
            "   - 类型（美术馆/街区/市场等）\n"
            "   - 一句话推荐理由\n"
            "   - 预估花费和距离\n\n"
            "输出要求：用 JSON 格式输出完整列表，方便下游工具直接消费。"
        ),
        expected_output=(
            "一个 JSON 数组，每个元素包含 name, type, description, "
            "estimated_cost_cny, distance_km 字段。"
            "同时附上人类可读的推荐列表文本。"
        ),
        agent=explorer,
    )


def create_decision_task(decision_maker: Agent, user_input: str) -> Task:
    """
    任务 2：精明决策
    Agent B 从 Agent A 的列表中筛选并点评
    """
    return Task(
        description=(
            f"用户需求：{user_input}\n\n"
            "你的任务：\n"
            "1. 拿到灵感探索者给出的推荐列表\n"
            "2. 使用 check_practicality 工具，验证每个地点的可行性\n"
            "3. 根据工具返回的结果，精选出最终 2-3 个推荐\n"
            "4. 对每个最终推荐，给出：\n"
            "   - 一句毒舌但中肯的评价\n"
            "   - 为什么值得去（不超过两句话）\n"
            "   - 一个实用小贴士（交通/时间/省钱技巧）\n"
            "5. 对被淘汰的选项，简要说明原因\n\n"
            "注意：你的点评要有个性，像一个本地朋友在给建议，不要像客服。"
        ),
        expected_output=(
            "最终推荐方案，包含 2-3 个精选地点，每个附有毒舌点评、"
            "推荐理由和实用贴士。以及被淘汰选项的简要说明。"
        ),
        agent=decision_maker,
        output_file="travel_plan.md",
    )

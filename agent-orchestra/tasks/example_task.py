from crewai import Task
from agents.example_agent import researcher, analyst, writer

# 示例任务定义
research_task = Task(
    description="""收集关于目标市场的信息，包括：
    1. 市场规模和增长趋势
    2. 主要竞争对手
    3. 消费者需求和偏好
    4. 市场机会和挑战""",
    expected_output="一份详细的市场调研报告，包含上述四个方面的分析。",
    agent=researcher,
)

analysis_task = Task(
    description="""分析市场调研数据，识别：
    1. 关键趋势和模式
    2. 机会和威胁
    3. 优势和劣势
    4. 建议和策略""",
    expected_output="一份数据分析报告，包含趋势分析、SWOT分析和策略建议。",
    agent=analyst,
)

writing_task = Task(
    description="""基于调研和分析结果，撰写一份完整的市场分析报告，包括：
    1. 执行摘要
    2. 市场概述
    3. 竞争分析
    4. 机会与挑战
    5. 建议与策略
    6. 结论""",
    expected_output="一份专业的市场分析报告，格式规范，内容完整。",
    agent=writer,
)
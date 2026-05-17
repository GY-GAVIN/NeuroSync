from crewai import Agent

# 示例智能体定义
researcher = Agent(
    role="研究员",
    goal="收集和分析目标市场的信息",
    backstory="""你是一位经验丰富的市场研究员，
    擅长收集和分析市场数据，为决策提供支持。""",
    verbose=True,
    allow_delegation=False,
)

analyst = Agent(
    role="分析师",
    goal="分析数据并提供洞察",
    backstory="""你是一位数据分析师，
    擅长从数据中发现模式和趋势，提供有价值的洞察。""",
    verbose=True,
    allow_delegation=False,
)

writer = Agent(
    role="撰稿人",
    goal="撰写清晰、专业的报告",
    backstory="""你是一位专业的撰稿人，
    擅长将复杂的信息转化为易于理解的报告。""",
    verbose=True,
    allow_delegation=False,
)
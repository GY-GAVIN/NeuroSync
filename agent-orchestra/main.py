#!/usr/bin/env python3
"""
Agent Orchestra - 多智能体协作示例
"""

from crewai import Crew, Process
from agents.example_agent import researcher, analyst, writer
from tasks.example_task import research_task, analysis_task, writing_task
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def main():
    """运行多智能体协作任务"""

    # 创建智能体团队
    crew = Crew(
        agents=[researcher, analyst, writer],
        tasks=[research_task, analysis_task, writing_task],
        process=Process.sequential,  # 顺序执行任务
        verbose=True,
    )

    # 执行任务
    print("🚀 开始执行多智能体协作任务...")
    result = crew.kickoff()

    # 输出结果
    print("\n" + "="*50)
    print("📊 执行结果：")
    print("="*50)
    print(result)

    return result

if __name__ == "__main__":
    main()
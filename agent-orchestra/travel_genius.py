#!/usr/bin/env python3
"""
Travel Genius - 双 Agent 旅行推荐系统
======================================

架构：
  用户输入 → [Agent A: 灵感探索者] → 原始推荐列表 → [Agent B: 精明决策者] → 最终方案

两个 Agent 各自使用独立的模型 API，通过 CrewAI 的顺序任务编排实现协作。
"""

import os
import sys
from dotenv import load_dotenv
from crewai import Crew, Process

# 加载环境变量
load_dotenv()


def run_travel_genius(
    destination: str = "东京",
    interests: str = "艺术 潮流 小众",
    budget: str = "中等",
    days: int = 5,
    preferences: str = "",
):
    """
    运行 Travel Genius 双 Agent 协作流程

    Args:
        destination: 目标城市
        interests: 兴趣关键词（空格分隔）
        budget: 预算等级（低/中等/高）
        days: 旅行天数
        preferences: 额外偏好说明
    """
    # 延迟导入，确保环境变量已加载
    from agents.travel_agents import build_explorer, build_decision_maker
    from tasks.travel_tasks import create_inspiration_task, create_decision_task

    # 组装用户输入
    user_input = (
        f"目的地：{destination}\n"
        f"兴趣：{interests}\n"
        f"预算：{budget}\n"
        f"天数：{days} 天\n"
    )
    if preferences:
        user_input += f"额外偏好：{preferences}\n"

    print("=" * 60)
    print("  Travel Genius - 双 Agent 旅行推荐系统")
    print("=" * 60)
    print(f"\n  目的地: {destination}")
    print(f"  兴趣: {interests}")
    print(f"  预算: {budget}")
    print(f"  天数: {days} 天")
    if preferences:
        print(f"  偏好: {preferences}")
    print("\n" + "=" * 60)

    # ── Step 1: 构建 Agent ──────────────────────────────────
    print("\n[1/4] 构建 Agent...")
    explorer = build_explorer()
    decision_maker = build_decision_maker()

    # ── Step 2: 创建任务 ────────────────────────────────────
    print("[2/4] 创建协作任务...")
    inspiration_task = create_inspiration_task(explorer, user_input)
    decision_task = create_decision_task(decision_maker, user_input)

    # ── Step 3: 组建 Crew ───────────────────────────────────
    print("[3/4] 组建 Crew（顺序执行模式）...")
    crew = Crew(
        agents=[explorer, decision_maker],
        tasks=[inspiration_task, decision_task],
        process=Process.sequential,
        verbose=True,
    )

    # ── Step 4: 执行 ────────────────────────────────────────
    print("[4/4] 开始执行...\n")
    print("-" * 60)
    result = crew.kickoff()

    # ── 输出结果 ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  最终旅行方案")
    print("=" * 60)
    print(result)

    # 保存结果
    output_file = "travel_plan.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# Travel Genius - {destination}旅行方案\n\n")
        f.write(f"- 目的地: {destination}\n")
        f.write(f"- 兴趣: {interests}\n")
        f.write(f"- 预算: {budget}\n")
        f.write(f"- 天数: {days} 天\n\n")
        f.write("---\n\n")
        f.write(str(result))
    print(f"\n方案已保存至 {output_file}")

    return result


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Travel Genius - 让两个 AI Agent 帮你规划旅行"
    )
    parser.add_argument("-d", "--destination", default="东京", help="目标城市")
    parser.add_argument("-i", "--interests", default="艺术 潮流 小众", help="兴趣关键词")
    parser.add_argument("-b", "--budget", default="中等", choices=["低", "中等", "高"], help="预算")
    parser.add_argument("-n", "--days", type=int, default=5, help="旅行天数")
    parser.add_argument("-p", "--preferences", default="", help="额外偏好")

    args = parser.parse_args()
    run_travel_genius(
        destination=args.destination,
        interests=args.interests,
        budget=args.budget,
        days=args.days,
        preferences=args.preferences,
    )


if __name__ == "__main__":
    main()

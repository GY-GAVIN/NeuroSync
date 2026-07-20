#!/usr/bin/env python3
"""
Stratego 弈策 — 博弈论多智能体决策助手
=======================================

让你的问题获得最严厉的博弈论剖析。

架构：
  用户情境 → [Agent 1: 博弈建模师] → 结构化模型 → [Agent 2: 均衡分析师] → 均衡结果 → [Agent 3: 策略顾问] → 行动建议

三个 Agent 各自使用独立的模型 API，通过 CrewAI 的顺序任务编排实现协作。
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from crewai import Crew, Process

load_dotenv()


def run_analysis(
    situation: str,
    verbose: bool = True,
    output_file: str | None = None,
) -> str:
    """
    运行 Stratego 三 Agent 协作分析流程。

    Args:
        situation: 用户描述的现实情境
        verbose: 是否输出详细日志
        output_file: 分析报告输出路径（默认 outputs/analysis_{timestamp}.md）
    """
    from agents.game_agents import build_modeler, build_analyst, build_advisor
    from tasks.game_tasks import create_modeling_task, create_analysis_task, create_advice_task

    print("=" * 60)
    print("  Stratego 弈策 — 博弈论多智能体决策助手")
    print("=" * 60)
    print(f"\n  情境: {situation[:80]}{'...' if len(situation) > 80 else ''}")
    print("=" * 60)

    # ── Step 1: 构建 Agent ──────────────────────────────────
    print("\n[1/5] 构建智能体...")
    modeler = build_modeler()
    analyst = build_analyst()
    advisor = build_advisor()
    print("  ✓ 博弈建模师 (Game Modeler)")
    print("  ✓ 均衡分析师 (Equilibrium Analyst)")
    print("  ✓ 策略顾问 (Strategy Advisor)")

    # ── Step 2: 创建任务 ────────────────────────────────────
    print("[2/5] 创建分析任务...")
    model_task = create_modeling_task(modeler, situation)
    analysis_task = create_analysis_task(analyst, situation)
    advice_task = create_advice_task(advisor, situation)
    print("  ✓ 博弈建模任务")
    print("  ✓ 均衡分析任务")
    print("  ✓ 策略建议任务")

    # ── Step 3: 组建 Crew ───────────────────────────────────
    print("[3/5] 组建分析团队（顺序执行模式）...")
    crew = Crew(
        agents=[modeler, analyst, advisor],
        tasks=[model_task, analysis_task, advice_task],
        process=Process.sequential,
        verbose=verbose,
    )

    # ── Step 4: 执行 ────────────────────────────────────────
    print("[4/5] 开始分析...\n")
    print("-" * 60)
    result = crew.kickoff()

    # ── Step 5: 输出结果 ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("  分析完成")
    print("=" * 60)
    print(result)

    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = output_file or f"outputs/analysis_{timestamp}.md"
    os.makedirs("outputs", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Stratego 弈策 — 博弈论分析报告\n\n")
        f.write(f"- 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"- 分析情境: {situation}\n\n")
        f.write("---\n\n")
        f.write(str(result))
    print(f"\n分析报告已保存至 {out_path}")

    return str(result)


DEFAULT_PRESETS = {
    "workplace": {
        "title": "职场博弈",
        "situation": (
            "我在一家互联网公司工作，和一个同事在竞争同一个晋升名额。"
            "我们俩能力相当，但那个同事经常在领导面前抢功劳，"
            "把我的想法说成是他的。我现在有两个选择："
            "一是也去抢功劳、搞办公室政治；二是专心做好自己的事，"
            "相信领导能看到真实贡献。我该怎么办？"
        ),
    },
    "pricing": {
        "title": "定价竞争",
        "situation": (
            "我在一条商业街上开了一家奶茶店，对面新开了一家竞争对手。"
            "现在我们都在考虑定价策略：定高价（25元）还是低价（15元）。"
            "如果两家都定高价，各自日利润3000元；"
            "如果我低价对方高价，我赚4500元，对方亏500元；"
            "反之我亏500元，对方赚4500元；"
            "两家都低价，各自日利润1500元。我该怎么定价？"
        ),
    },
    "negotiation": {
        "title": "谈判策略",
        "situation": (
            "我在和一家公司谈一份工作合同。"
            "对方给出的薪资低于我的预期。"
            "我有另一个工作机会（薪资中等但发展空间较小）作为备选。"
            "我应该在薪资上坚持底线，还是接受对方的条件先入职再说？"
        ),
    },
    "relationship": {
        "title": "情侣关系",
        "situation": (
            "我和女朋友在决定周末去哪里玩。"
            "我想去看新上映的动作片，她想去逛艺术展。"
            "我们其实都更愿意一起去（而不是各自行动），"
            "但各自偏好不同的活动。"
            "如果各去各的，双方体验都不好。我该怎么选？"
        ),
    },
}


def main():
    """命令行入口。"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Stratego 弈策 — 让你的问题获得最严厉的博弈论剖析"
    )
    parser.add_argument("situation", nargs="?", default="", help="需要分析的现实情境")
    parser.add_argument(
        "-p", "--preset", choices=list(DEFAULT_PRESETS.keys()),
        help="使用预设场景（替代直接输入情境）"
    )
    parser.add_argument("-o", "--output", default="", help="分析报告输出路径")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式（减少日志）")
    parser.add_argument(
        "--list-presets", action="store_true", help="列出所有预设场景"
    )

    args = parser.parse_args()

    if args.list_presets:
        print("可用的预设场景：\n")
        for key, preset in DEFAULT_PRESETS.items():
            print(f"  {key:15s} - {preset['title']}")
            print(f"  {'':15s}   {preset['situation'][:60]}...")
            print()
        return

    # 确定分析情境
    situation = args.situation.strip()
    if args.preset:
        situation = DEFAULT_PRESETS[args.preset]["situation"]
        print(f"\n📌 使用预设场景: {DEFAULT_PRESETS[args.preset]['title']}\n")

    if not situation:
        print("请提供需要分析的情境，或使用 --preset 选择预设场景。")
        parser.print_help()
        sys.exit(1)

    run_analysis(
        situation=situation,
        verbose=not args.quiet,
        output_file=args.output or None,
    )


if __name__ == "__main__":
    main()

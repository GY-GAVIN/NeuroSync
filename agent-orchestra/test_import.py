#!/usr/bin/env python3
"""
测试导入是否正常
"""

def test_imports():
    """测试所有模块是否可以正常导入"""
    try:
        print("测试导入 agents.example_agent...")
        from agents.example_agent import researcher, analyst, writer
        print("✅ agents.example_agent 导入成功")

        print("测试导入 tasks.example_task...")
        from tasks.example_task import research_task, analysis_task, writing_task
        print("✅ tasks.example_task 导入成功")

        print("测试导入 tools.example_tool...")
        from tools.example_tool import WebSearchTool, DataAnalysisTool, ReportGeneratorTool
        print("✅ tools.example_tool 导入成功")

        print("测试导入 crewai...")
        from crewai import Crew, Process
        print("✅ crewai 导入成功")

        print("测试导入 langchain...")
        from langchain_core.language_models import BaseLLM
        print("✅ langchain 导入成功")

        print("测试导入 streamlit...")
        import streamlit as st
        print("✅ streamlit 导入成功")

        print("测试导入 python-dotenv...")
        from dotenv import load_dotenv
        print("✅ python-dotenv 导入成功")

        print("\n🎉 所有导入测试通过！")
        return True

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False

if __name__ == "__main__":
    test_imports()
import streamlit as st
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 页面配置
st.set_page_config(
    page_title="Agent Orchestra",
    page_icon="🤖",
    layout="wide"
)

# 主标题
st.title("🤖 Agent Orchestra")
st.markdown("基于 CrewAI 和 LangChain 的多智能体协作系统")

# 侧边栏
with st.sidebar:
    st.header("配置")
    api_key = st.text_input("OpenAI API Key", type="password",
                           value=os.getenv("OPENAI_API_KEY", ""))

    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("API Key 已配置")

    st.divider()

    st.header("关于")
    st.markdown("""
    **Agent Orchestra** 是一个多智能体协作框架，支持：

    - 🎭 多智能体角色定义
    - 📋 任务编排与分配
    - 🔧 工具集成
    - 📊 结果可视化
    """)

# 主界面
tab1, tab2, tab3 = st.tabs(["智能体", "任务", "执行"])

with tab1:
    st.header("智能体管理")
    st.info("在此定义和管理您的智能体角色")

    # 示例智能体列表
    agents = [
        {"name": "研究员", "role": "负责信息收集和研究", "status": "就绪"},
        {"name": "分析师", "role": "负责数据分析和洞察", "status": "就绪"},
        {"name": "撰稿人", "role": "负责内容创作和编辑", "status": "就绪"},
    ]

    for agent in agents:
        with st.expander(f"{agent['name']} - {agent['role']}"):
            st.write(f"**状态:** {agent['status']}")
            st.write(f"**角色:** {agent['role']}")

with tab2:
    st.header("任务管理")
    st.info("在此定义和管理您的任务")

    # 示例任务
    tasks = [
        {"name": "市场调研", "description": "收集目标市场信息", "assigned_to": "研究员"},
        {"name": "数据分析", "description": "分析调研数据", "assigned_to": "分析师"},
        {"name": "报告撰写", "description": "撰写分析报告", "assigned_to": "撰稿人"},
    ]

    for task in tasks:
        with st.expander(f"{task['name']}"):
            st.write(f"**描述:** {task['description']}")
            st.write(f"**负责人:** {task['assigned_to']}")

with tab3:
    st.header("执行控制")
    st.info("在此启动和监控智能体协作")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🚀 开始执行", use_container_width=True):
            st.warning("执行功能待实现")

    with col2:
        if st.button("⏸️ 暂停", use_container_width=True):
            st.warning("暂停功能待实现")

    with col3:
        if st.button("🔄 重置", use_container_width=True):
            st.warning("重置功能待实现")

    # 执行日志
    st.divider()
    st.subheader("执行日志")
    st.code("等待执行...")

# 页脚
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <p>Agent Orchestra v0.1.0 | 基于 CrewAI 和 LangChain 构建</p>
</div>
""", unsafe_allow_html=True)
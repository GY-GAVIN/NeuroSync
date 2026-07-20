"""
Stratego 弈策 — Streamlit 前端
深色主题 · 分步分析展示 · 博弈矩阵可视化
"""

import json
import os
import re
import time
from datetime import datetime

import streamlit as st

from dotenv import load_dotenv
from main import run_analysis, DEFAULT_PRESETS

load_dotenv()

# ── 页面配置 ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Stratego 弈策",
    page_icon="♟️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 自定义 CSS ───────────────────────────────────────────────
st.markdown("""
<style>
    /* 全局主题 */
    .stApp { background-color: #1E1E2E; color: #CDD6F4; }
    h1, h2, h3 { color: #89B4FA !important; font-weight: 600; }
    h1 { font-size: 1.8rem !important; }
    h2 { font-size: 1.4rem !important; border-bottom: 1px solid #313244; padding-bottom: 0.5rem; }
    h3 { font-size: 1.1rem !important; color: #A6E3A1 !important; }

    /* 卡片容器 */
    .card {
        background-color: #313244;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        border: 1px solid #45475A;
    }
    .card h3 { margin-top: 0; }

    /* 步骤指示器 */
    .step-done { color: #A6E3A1; }
    .step-active { color: #F9E2AF; }
    .step-pending { color: #585B70; }

    /* 收益矩阵表格 */
    .matrix-table {
        border-collapse: collapse;
        margin: 1rem 0;
        font-size: 0.95rem;
        width: 100%;
    }
    .matrix-table th, .matrix-table td {
        border: 1px solid #45475A;
        padding: 10px 16px;
        text-align: center;
    }
    .matrix-table th {
        background-color: #45475A;
        color: #CDD6F4;
        font-weight: 600;
    }
    .matrix-table td { background-color: #1E1E2E; }
    .matrix-table .row-label {
        background-color: #313244;
        font-weight: 600;
        color: #89B4FA;
        text-align: right;
    }
    .matrix-table .col-label {
        background-color: #313244;
        font-weight: 600;
        color: #89B4FA;
    }
    .matrix-table .equilibrium {
        background-color: rgba(166, 227, 161, 0.15);
        border: 2px solid #A6E3A1;
    }

    /* 均衡高亮标签 */
    .eq-badge {
        display: inline-block;
        background-color: #A6E3A1;
        color: #1E1E2E;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-left: 4px;
    }
    .pareto-badge {
        display: inline-block;
        background-color: #F9E2AF;
        color: #1E1E2E;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
    }

    /* Agent 输出框 */
    .agent-output {
        background-color: #1E1E2E;
        border-left: 3px solid #89B4FA;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
        line-height: 1.6;
        white-space: pre-wrap;
        font-family: 'Courier New', monospace;
    }
    .agent-output.modeler { border-left-color: #89B4FA; }
    .agent-output.analyst { border-left-color: #F9E2AF; }
    .agent-output.advisor { border-left-color: #A6E3A1; }

    /* 预设按钮 */
    .preset-btn {
        background-color: #313244;
        border: 1px solid #45475A;
        border-radius: 8px;
        padding: 8px 16px;
        color: #CDD6F4;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.85rem;
    }
    .preset-btn:hover {
        border-color: #89B4FA;
        background-color: #45475A;
    }

    /* 分割线 */
    hr {
        border-color: #313244 !important;
        margin: 1.5rem 0 !important;
    }

    /* 页脚 */
    .footer {
        text-align: center;
        color: #585B70;
        font-size: 0.8rem;
        padding: 2rem 0;
    }

    /* stStatus 内的样式 */
    [data-testid="stStatusWidget"] { background-color: #313244; border: 1px solid #45475A; }

    /* 滚动条 */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #1E1E2E; }
    ::-webkit-scrollbar-thumb { background: #45475A; border-radius: 4px; }

    /* 代码块 */
    code {
        background-color: #45475A;
        color: #F5C2E7;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85em;
    }
</style>
""", unsafe_allow_html=True)


# ── 会话状态初始化 ──────────────────────────────────────────

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "analysis_running" not in st.session_state:
    st.session_state.analysis_running = False
if "situation" not in st.session_state:
    st.session_state.situation = ""
if "current_step" not in st.session_state:
    st.session_state.current_step = 0


# ── 辅助函数 ─────────────────────────────────────────────────

def parse_payoff_matrix(text: str) -> dict | None:
    """从 Agent 输出文本中提取 JSON 格式的收益矩阵。"""
    # 尝试提取 JSON 块
    patterns = [
        r'```json\s*({.*?})\s*```',
        r'(\{"players":.*?"payoffs":.*?\})',
        r'("players"\s*:.*?"payoffs"\s*:.*?\})',
    ]
    for pat in patterns:
        match = re.search(pat, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    return None


def render_matrix(matrix_data: dict):
    """渲染收益矩阵为 HTML 表格。"""
    try:
        players = matrix_data.get("players", ["P1", "P2"])
        strategies = matrix_data.get("strategies", {})
        payoffs = matrix_data.get("payoffs", {})

        p1_strats = strategies.get(players[0], [])
        p2_strats = strategies.get(players[1], [])
        p1_pay = list(payoffs.values())[0]
        p2_pay = list(payoffs.values())[1]

        # 检测均衡（通过 Nash 求解器结果或手动标记）
        nash_cells = set()

        html = '<table class="matrix-table">'

        # 表头
        html += '<tr><th></th><th></th>'
        for s in p2_strats:
            html += f'<th class="col-label">{s}</th>'
        html += '</tr>'

        html += '<tr><th></th><th></th>'
        for _ in p2_strats:
            html += f'<th class="col-label" style="font-size:0.7rem;color:#585B70;">→ {players[1]}</th>'
        html += '</tr>'

        # 数据行
        for i, s1 in enumerate(p1_strats):
            html += f'<tr><th class="row-label" style="font-size:0.7rem;color:#585B70;">{players[0]} →</th>'
            html += f'<th class="row-label">{s1}</th>'
            for j in range(len(p2_strats)):
                eq_class = "equilibrium" if (i, j) in nash_cells else ""
                p1_v = p1_pay[i][j] if isinstance(p1_pay[i], (list, tuple)) else p1_pay[i]
                p2_v = p2_pay[i][j] if isinstance(p2_pay[j], (list, tuple)) else p2_pay[i] if isinstance(p2_pay[i], (list, tuple)) else p2_pay[i][j]

                cell_content = f"({p1_v}, {p2_v})"
                html += f'<td class="{eq_class}">{cell_content}</td>'
            html += '</tr>'

        html += '<tr><td colspan="2" style="text-align:right;font-size:0.7rem;color:#585B70;border:none;padding-top:4px;">↑ {}</td>'.format(players[0])
        html += '<td colspan="{}" style="text-align:left;font-size:0.7rem;color:#585B70;border:none;padding-top:4px;">← {}</td>'.format(len(p2_strats), players[1])
        html += '</tr>'
        html += '</table>'

        return html
    except Exception:
        return None


def extract_section(text: str, section_name: str) -> str:
    """从 Agent 输出中提取特定章节。"""
    patterns = [
        rf"###?\s*步骤\s*{section_name}[：:]\s*(.*?)(?=###?\s*步骤|\Z)",
        rf"###?\s*{section_name}[：:]\s*(.*?)(?=###?\s*|\Z)",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.DOTALL)
        if match:
            return match.group(1).strip()
    return ""


# ── 侧边栏 ───────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ 模型配置")
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="所有 Agent 的默认 API Key",
    )
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("已配置")

    st.divider()

    st.markdown("### 📋 预设场景")
    for key, preset in DEFAULT_PRESETS.items():
        if st.button(
            f"📌 {preset['title']}",
            key=f"preset_{key}",
            use_container_width=True,
        ):
            st.session_state.situation = preset["situation"]
            st.rerun()

    st.divider()

    st.markdown("### ℹ️ 关于")
    st.markdown("""
    **Stratego 弈策** v0.1.0

    基于 CrewAI 的三 Agent 博弈论分析系统。
    参考《策略博弈》(Dixit & Skeath) 理论框架。
    """)

    if st.button("🗑️ 清空结果", use_container_width=True):
        st.session_state.analysis_result = None
        st.session_state.analysis_running = False
        st.session_state.current_step = 0
        st.rerun()


# ── 主界面 ───────────────────────────────────────────────────

# 头部
col_logo, col_title = st.columns([0.08, 1])
with col_logo:
    st.markdown("<h1 style='font-size:2rem;'>♟️</h1>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='margin-bottom:0;'>Stratego 弈策</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#585B70;margin-top:-8px;'>"
        "博弈论多智能体决策助手 · 用博弈的视角看世界</p>",
        unsafe_allow_html=True,
    )

# 情境输入
st.markdown("### 📝 描述你的情境")

situation = st.text_area(
    "你在面对什么困境？告诉我具体情况，我来帮你用博弈论分析。",
    value=st.session_state.situation,
    height=140,
    placeholder=(
        "例如：我在一家互联网公司工作，和一个同事在竞争同一个晋升名额。"
        "那个同事经常在领导面前抢功劳...我该和他一样去抢功，还是专心做事？"
    ),
    label_visibility="collapsed",
)

col_start, col_status = st.columns([1, 4])
with col_start:
    start_btn = st.button(
        "▶️ 开始分析",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.analysis_running,
    )
with col_status:
    if st.session_state.analysis_running:
        st.markdown(
            "<span style='color:#F9E2AF;'>⏳ 分析进行中，请稍候...</span>",
            unsafe_allow_html=True,
        )

# ── 执行分析 ─────────────────────────────────────────────────

if start_btn and situation.strip():
    st.session_state.analysis_running = True
    st.session_state.analysis_result = None

    # 显示分析进度
    status_container = st.status("分析中...", expanded=True, state="running")

    with status_container:
        progress_bar = st.progress(0, text="初始化分析...")

        def update_progress(step: int, text: str):
            pct = min(step * 33, 99)
            progress_bar.progress(pct, text=text)

        try:
            update_progress(1, "⚙️ 博弈建模师 工作中...")
            result = run_analysis(situation, verbose=False)

            update_progress(3, "✅ 分析完成")
            progress_bar.progress(100, text="✅ 分析完成")

            st.session_state.analysis_result = result
            status_container.update(label="分析完成", state="complete", expanded=False)

        except Exception as e:
            status_container.update(label="分析失败", state="error", expanded=True)
            st.error(f"分析过程中出现错误: {e}")
            st.exception(e)
        finally:
            st.session_state.analysis_running = False
            st.rerun()

elif start_btn and not situation.strip():
    st.warning("请先描述你的情境")

# ── 显示结果 ─────────────────────────────────────────────────

if st.session_state.analysis_result:
    result_text = st.session_state.analysis_result

    st.markdown("---")
    st.markdown("## 📊 分析结果")

    # 三个步骤的折叠展示
    with st.expander("**1/3 ⚙️ 博弈建模** — Game Modeler", expanded=True):
        st.markdown('<div class="agent-output modeler">', unsafe_allow_html=True)
        # 尝试展示收益矩阵
        matrix_data = parse_payoff_matrix(result_text)
        if matrix_data:
            matrix_html = render_matrix(matrix_data)
            if matrix_html:
                st.markdown("#### 收益矩阵")
                st.markdown(matrix_html, unsafe_allow_html=True)
                st.markdown("---")
        st.markdown(result_text)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("**2/3 📊 均衡分析** — Equilibrium Analyst", expanded=False):
        st.markdown('<div class="agent-output analyst">', unsafe_allow_html=True)
        st.markdown(result_text)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("**3/3 💡 策略建议** — Strategy Advisor", expanded=False):
        st.markdown('<div class="agent-output advisor">', unsafe_allow_html=True)
        st.markdown(result_text)
        st.markdown('</div>', unsafe_allow_html=True)

    # 导出
    st.markdown("---")
    col_export1, col_export2 = st.columns([1, 5])
    with col_export1:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"stratego_report_{timestamp}.md"
        st.download_button(
            label="📥 导出完整报告",
            data=result_text,
            file_name=report_filename,
            mime="text/markdown",
            use_container_width=True,
        )
    with col_export2:
        st.markdown(
            f"<span style='color:#585B70;font-size:0.85rem;'>Markdown 格式 · {len(result_text)} 字符</span>",
            unsafe_allow_html=True,
        )


# ── 初始引导（无结果时） ──────────────────────────────────────

if not st.session_state.analysis_result and not st.session_state.analysis_running:
    st.markdown("---")

    col_guide1, col_guide2, col_guide3 = st.columns(3)

    with col_guide1:
        st.markdown("""
        <div class="card">
            <h3>⚠️ 博弈建模</h3>
            <p style="color:#A6ADC8;font-size:0.9rem;">
            你的故事将被转化为规范的博弈模型——参与者、策略、收益，一目了然。
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_guide2:
        st.markdown("""
        <div class="card">
            <h3>🎯 均衡分析</h3>
            <p style="color:#A6ADC8;font-size:0.9rem;">
            计算 Nash 均衡、占优策略、Pareto 前沿——看清你真正面临的选择。
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_guide3:
        st.markdown("""
        <div class="card">
            <h3>💡 策略建议</h3>
            <p style="color:#A6ADC8;font-size:0.9rem;">
            得到可执行的行动方案——承诺、信号、BATNA，每一步都有依据。
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;padding:1rem;">
        <p style="color:#585B70;">
        ♟️ 输入你的困境，或点击左侧预设场景快速开始
        </p>
    </div>
    """, unsafe_allow_html=True)


# ── 页脚 ─────────────────────────────────────────────────────

st.markdown("---")
st.markdown("""
<div class="footer">
    <p>Stratego 弈策 v0.1.0 · 基于 CrewAI 和《策略博弈》理论框架</p>
    <p style="color:#45475A;font-size:0.75rem;">博弈论不给你答案，它给你思考的框架。</p>
</div>
""", unsafe_allow_html=True)

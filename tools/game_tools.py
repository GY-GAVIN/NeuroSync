"""
NeuroSync — 博弈论计算工具

提供六个核心工具（前两个为 LLM/规则辅助，后四个为纯算法）：
  - build_payoff_matrix：验证并规范化收益矩阵 JSON 格式
  - identify_game_type：基于收益结构分类博弈类型
  - solve_pure_nash：暴力搜索纯策略 Nash 均衡
  - solve_mixed_nash：代数法求解 2×2 混合策略均衡
  - check_dominance：占优策略识别
  - pareto_analysis：Pareto 最优分析

所有工具遵循 CrewAI BaseTool + Pydantic args_schema 模式。
"""

import json
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# ── 类型别名 ─────────────────────────────────────────────────

Matrix = dict[str, list[list[float]]]
"""格式：{"players": ["P1","P2"], "strategies": {"P1": [...], "P2": [...]},
         "payoffs": {"P1": [[a,b],[c,d]], "P2": [[e,f],[g,h]]}}"""


# ── 输入 Schema ──────────────────────────────────────────────

class PayoffMatrixInput(BaseModel):
    players: list[str] = Field(..., min_length=2, max_length=4,
                               description="参与者名称列表，如 ['你', '同事']")
    strategies: dict[str, list[str]] = Field(
        ..., description="每个参与者的策略列表，如 {'你': ['合作','背叛'], '同事': ['合作','背叛']}"
    )
    payoffs: dict[str, list[list[float]]] = Field(
        ..., description="收益矩阵，格式：{'P1': [[a,b],[c,d]], 'P2': [[e,f],[g,h]]}"
    )


class GameTypeInput(BaseModel):
    payoff_matrix: str = Field(..., description="JSON 格式的收益矩阵")
    is_sequential: bool = Field(default=False, description="是否顺序博弈")
    is_repeated: bool = Field(default=False, description="是否重复博弈")
    is_complete_info: bool = Field(default=True, description="是否完全信息")


class PayoffMatrixStr(BaseModel):
    payoff_matrix: str = Field(..., description="JSON 格式的收益矩阵")


# ── 内部工具函数 ────────────────────────────────────────────

def _parse_matrix(payoff_matrix: str) -> dict:
    """解析并验证收益矩阵 JSON。"""
    try:
        data = json.loads(payoff_matrix)
    except json.JSONDecodeError as e:
        raise ValueError(f"收益矩阵 JSON 解析失败: {e}")

    required = {"players", "strategies", "payoffs"}
    if not required.issubset(data.keys()):
        raise ValueError(f"收益矩阵必须包含字段: {required}，当前: {set(data.keys())}")

    return data


def _n_players(data: dict) -> int:
    return len(data["players"])


def _n_strategies(data: dict) -> int:
    return [len(s) for s in data["strategies"].values()]


def _validate_2player(data: dict):
    """确保是 2 人博弈，否则抛错。"""
    n = _n_players(data)
    if n != 2:
        raise ValueError(f"该工具仅支持 2 人博弈，当前参与者数量: {n}")


def _p1_payoffs(data: dict) -> list[list[float]]:
    return data["payoffs"]["P1"] if "P1" in data["payoffs"] else list(data["payoffs"].values())[0]


def _p2_payoffs(data: dict) -> list[list[float]]:
    return data["payoffs"]["P2"] if "P2" in data["payoffs"] else list(data["payoffs"].values())[1]


# ── Tool 1: 构建并验证收益矩阵 ───────────────────────────────

class BuildPayoffMatrixTool(BaseTool):
    name: str = "build_payoff_matrix"
    description: str = (
        "验证并规范化收益矩阵的 JSON 格式。"
        "输入参与者、策略和收益值，输出标准化的 JSON 矩阵供下游工具使用。"
    )
    args_schema: Type[BaseModel] = PayoffMatrixInput

    def _run(self, players: list[str], strategies: dict[str, list[str]],
             payoffs: dict[str, list[list[float]]]) -> str:
        result = {
            "players": players,
            "strategies": strategies,
            "payoffs": payoffs,
        }
        # 基础校验
        n_rows = len(payoffs[list(payoffs.keys())[0]])
        n_cols = len(payoffs[list(payoffs.keys())[0]][0]) if n_rows > 0 else 0
        n_p1_strats = len(strategies[players[0]])
        n_p2_strats = len(strategies[players[1]]) if len(players) > 1 else 0

        assert n_rows == n_p1_strats, f"行数 {n_rows} 与 P1 策略数 {n_p1_strats} 不匹配"
        assert n_cols == n_p2_strats, f"列数 {n_cols} 与 P2 策略数 {n_p2_strats} 不匹配"

        result["_meta"] = {
            "type": f"{n_rows}×{n_cols} 博弈",
            "players_count": len(players),
        }
        return json.dumps(result, ensure_ascii=False, indent=2)


# ── Tool 2: 识别博弈类型 ────────────────────────────────────

class IdentifyGameTypeTool(BaseTool):
    name: str = "identify_game_type"
    description: str = (
        "根据收益矩阵的结构特征，识别博弈所属的经典类型。"
        "支持识别：囚徒困境、斗鸡博弈、猎鹿博弈、性别战、协调博弈、零和博弈等。"
    )
    args_schema: Type[BaseModel] = GameTypeInput

    def _run(self, payoff_matrix: str, is_sequential: bool = False,
             is_repeated: bool = False, is_complete_info: bool = True) -> str:
        try:
            data = _parse_matrix(payoff_matrix)
            _validate_2player(data)
        except ValueError as e:
            return json.dumps({"error": str(e), "classification": "无法分类"}, ensure_ascii=False)

        p1 = _p1_payoffs(data)
        p2 = _p2_payoffs(data)

        # 经典 2×2 博弈收益命名 (P1 行 P2 列):
        #           P2: L      R
        #   P1: U   (a1,a2)  (b1,b2)
        #   P1: D   (c1,c2)  (d1,d2)
        try:
            a1, a2 = p1[0][0], p2[0][0]
            b1, b2 = p1[0][1], p2[0][1]
            c1, c2 = p1[1][0], p2[1][0]
            d1, d2 = p1[1][1], p2[1][1]
        except (IndexError, TypeError):
            return json.dumps({"error": "无法解析 2×2 矩阵", "classification": "无法分类"}, ensure_ascii=False)

        # ── 博弈类型分类（基于属性而非固定排序） ─────────────
        classifications = []
        details = []
        tol = 0.01

        def _strictly_dominated(p: list[list[float]], i: int, j: int) -> bool:
            """策略 i 是否严格劣于策略 j（行玩家）。"""
            return all(p[i][k] < p[j][k] for k in range(len(p[0])))

        def _strictly_dominant(p: list[list[float]], i: int) -> bool:
            """策略 i 是否为严格占优策略（行玩家）。"""
            return all(all(p[i][k] > p[j][k] for k in range(len(p[0]))) for j in range(len(p)) if j != i)

        def _pareto_dominates(ai: int, aj: int, bi: int, bj: int) -> bool:
            """结果 (ai,aj) 是否 Pareto 占优 (bi,bj)。"""
            p1_a, p2_a = p1[ai][aj], p2[ai][aj]
            p1_b, p2_b = p1[bi][bj], p2[bi][bj]
            return (p1_a >= p1_b and p2_a >= p2_b) and (p1_a > p1_b or p2_a > p2_b)

        # 零和检查
        is_zs = all(
            abs(p1[i][j] + p2[i][j]) < tol
            for i in range(len(p1)) for j in range(len(p1[0]))
        )

        # 计算纯策略 Nash 均衡
        nash_cells = []
        for i in range(len(p1)):
            for j in range(len(p1[0])):
                p1_br = all(p1[i][j] >= p1[k][j] for k in range(len(p1)))
                p2_br = all(p2[i][j] >= p2[i][k] for k in range(len(p1[0])))
                if p1_br and p2_br:
                    nash_cells.append((i, j))

        # 计算占优关系
        p1_has_dominant = any(_strictly_dominant(p1, i) for i in range(len(p1)))
        p2_has_dominant = any(_strictly_dominant(p2, i) for i in range(len(p2)))

        n = len(nash_cells)

        # ── 零和博弈 ─────────────────────────────────────────
        if is_zs:
            classifications.append("零和博弈 (Zero-sum)")
            details.append("一方的收益恰好是另一方的损失，利益完全对立")

        # ── 囚徒困境 ─────────────────────────────────────────
        # 双方都有严格占优策略，且占优策略均衡被另一个结果 Pareto 占优
        if p1_has_dominant and p2_has_dominant and n == 1:
            eq = nash_cells[0]
            other_cells = [(i, j) for i in range(len(p1)) for j in range(len(p1[0])) if (i, j) != eq]
            if any(_pareto_dominates(*other, *eq) for other in other_cells):
                classifications.append("囚徒困境 (Prisoner's Dilemma)")
                details.append("个人理性导致集体非理性：双方都有占优策略（背叛），但合作结果对双方更好")

        # ── 斗鸡博弈 ─────────────────────────────────────────
        # 2 个纯策略均衡，且在对角线两侧（非对角线上）
        if n == 2:
            # 检查均衡是否在对角线两侧（非对称均衡）
            eq0, eq1 = nash_cells
            diag0 = eq0[0] == eq0[1]
            diag1 = eq1[0] == eq1[1]
            if diag0 and diag1:
                # 两个均衡都在对角线上 → 协调博弈/性别战/猎鹿
                (a, b), (c, d) = nash_cells
                p1_pref_a = p1[a][b] > p1[c][d]
                p2_pref_a = p2[a][b] > p2[c][d]

                if p1_pref_a and not p2_pref_a:
                    # P1 偏好一个，P2 偏好另一个 → 性别战
                    classifications.append("性别战 (Battle of the Sexes)")
                    details.append("双方都想协调但偏好不同的协调结果")
                elif p1_pref_a and p2_pref_a:
                    # 双方偏好同一个均衡 → 猎鹿博弈或纯协调
                    if _pareto_dominates(a, b, c, d) or _pareto_dominates(c, d, a, b):
                        classifications.append("猎鹿博弈 (Stag Hunt)")
                        details.append("合作有更大收益但存在风险——需要信任对方也会合作")
                    else:
                        classifications.append("协调博弈 (Coordination)")
                        details.append("双方偏好相同的协调点，没有利益冲突")
                else:
                    classifications.append("一般协调博弈 (Coordination)")
                    details.append("存在多个均衡，需通过协调解决")
            else:
                # 均衡在非对角线上 → 斗鸡博弈
                classifications.append("斗鸡博弈 (Chicken)")
                details.append("双方都想展示强硬，但都强硬时结果最糟。谁先退让成为关键")

        # 如果没有任何分类命中
        if not classifications:
            classifications.append("一般非合作博弈 (General Non-cooperative Game)")
            details.append("该博弈不匹配经典类型，需具体分析收益结构")

        # 补充修饰
        modifiers = []
        if is_zs:
            modifiers.append("零和博弈")
        if is_sequential:
            modifiers.append("顺序博弈")
        else:
            modifiers.append("同时行动")
        if is_repeated:
            modifiers.append("重复博弈")
        if not is_complete_info:
            modifiers.append("不完全信息")
        modifiers.append("完全信息" if is_complete_info else None)
        modifiers = [m for m in modifiers if m]

        result = {
            "classifications": classifications,
            "details": details,
            "modifiers": modifiers,
            "is_zero_sum": is_zs,
            "is_sequential": is_sequential,
            "is_repeated": is_repeated,
            "is_complete_information": is_complete_info,
            "summary": f"{' · '.join(modifiers)} — {' / '.join(classifications)}",
        }
        return json.dumps(result, ensure_ascii=False, indent=2)


# ── Tool 3: 纯策略 Nash 均衡求解器 ─────────────────────────

class SolvePureNashTool(BaseTool):
    name: str = "solve_pure_nash"
    description: str = (
        "暴力搜索纯策略 Nash 均衡。"
        "对每个策略组合，检查是否有任何参与者可以通过单方面偏离获得更高收益。"
        "支持 2 人博弈，返回所有纯策略均衡及其最佳回应标注。"
    )
    args_schema: Type[BaseModel] = PayoffMatrixStr

    def _run(self, payoff_matrix: str) -> str:
        try:
            data = _parse_matrix(payoff_matrix)
            _validate_2player(data)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

        p1 = _p1_payoffs(data)
        p2 = _p2_payoffs(data)
        p1_strats = data["strategies"][data["players"][0]]
        p2_strats = data["strategies"][data["players"][1]]

        rows = len(p1)
        cols = len(p1[0])
        equilibria = []
        br_matrix = []  # 最佳回应标注

        for i in range(rows):
            br_row = []
            for j in range(cols):
                # P1 最佳回应检查
                p1_best = all(p1[i][j] >= p1[k][j] for k in range(rows))
                # P2 最佳回应检查
                p2_best = all(p2[i][j] >= p2[i][k] for k in range(cols))

                is_eq = p1_best and p2_best

                br_row.append({
                    "cell": f"({p1_strats[i]}, {p2_strats[j]})",
                    "p1_payoff": p1[i][j],
                    "p2_payoff": p2[i][j],
                    "p1_best_response": p1_best,
                    "p2_best_response": p2_best,
                    "is_nash_equilibrium": is_eq,
                })

                if is_eq:
                    equilibria.append({
                        "strategies": {"P1": p1_strats[i], "P2": p2_strats[j]},
                        "payoffs": [p1[i][j], p2[i][j]],
                        "description": f"P1 选择「{p1_strats[i]}」, P2 选择「{p2_strats[j]}」→ ({p1[i][j]}, {p2[i][j]})",
                    })
            br_matrix.append(br_row)

        result = {
            "equilibria": equilibria,
            "count": len(equilibria),
            "best_response_matrix": br_matrix,
            "summary": (
                f"找到 {len(equilibria)} 个纯策略 Nash 均衡"
                if equilibria else "未找到纯策略 Nash 均衡（可尝试混合策略）"
            ),
        }
        return json.dumps(result, ensure_ascii=False, indent=2)


# ── Tool 4: 混合策略 Nash 均衡求解器（仅 2×2）─────────────

class SolveMixedNashTool(BaseTool):
    name: str = "solve_mixed_nash"
    description: str = (
        "求解 2×2 双人博弈的混合策略 Nash 均衡。"
        "使用标准代数公式：p = (d2-c2)/(a2-b2-c2+d2), q = (d1-b1)/(a1-b1-c1+d1)。"
        "非 2×2 的博弈返回错误信息，由 Agent 自行推理。"
    )
    args_schema: Type[BaseModel] = PayoffMatrixStr

    def _run(self, payoff_matrix: str) -> str:
        try:
            data = _parse_matrix(payoff_matrix)
            _validate_2player(data)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

        p1 = _p1_payoffs(data)
        p2 = _p2_payoffs(data)

        rows, cols = len(p1), len(p1[0])
        if rows != 2 or cols != 2:
            return json.dumps({
                "error": f"混合策略公式仅支持 2×2 博弈（当前 {rows}×{cols}）",
                "note": "请 Agent 自行推导混合策略均衡",
            }, ensure_ascii=False)

        try:
            a1, a2 = p1[0][0], p2[0][0]
            b1, b2 = p1[0][1], p2[0][1]
            c1, c2 = p1[1][0], p2[1][0]
            d1, d2 = p1[1][1], p2[1][1]
        except (IndexError, TypeError):
            return json.dumps({"error": "无法解析矩阵数据"}, ensure_ascii=False)

        # P1 选择混合策略 (p, 1-p): p = (d2 - c2) / (a2 - b2 - c2 + d2)
        denom_p = a2 - b2 - c2 + d2
        if abs(denom_p) < 1e-10:
            p = None  # 退化解
        else:
            p_raw = (d2 - c2) / denom_p
            p = max(0.0, min(1.0, p_raw))

        # P2 选择混合策略 (q, 1-q): q = (d1 - b1) / (a1 - b1 - c1 + d1)
        denom_q = a1 - b1 - c1 + d1
        if abs(denom_q) < 1e-10:
            q = None
        else:
            q_raw = (d1 - b1) / denom_q
            q = max(0.0, min(1.0, q_raw))

        # 计算期望收益
        if p is not None and q is not None:
            exp_p1 = (p * q * a1 + p * (1 - q) * b1 +
                      (1 - p) * q * c1 + (1 - p) * (1 - q) * d1)
            exp_p2 = (p * q * a2 + p * (1 - q) * b2 +
                      (1 - p) * q * c2 + (1 - p) * (1 - q) * d2)
        else:
            exp_p1 = exp_p2 = None

        p1_strats = data["strategies"][data["players"][0]]
        p2_strats = data["strategies"][data["players"][1]]

        result = {
            "mixed_equilibrium": {
                "P1_mix": {
                    "description": f"以概率 {p:.3f} 选择「{p1_strats[0]}」，{(1-p):.3f} 选择「{p1_strats[1]}」" if p is not None else "退化解",
                    "probabilities": [round(p, 4), round(1 - p, 4)] if p is not None else None,
                },
                "P2_mix": {
                    "description": f"以概率 {q:.3f} 选择「{p2_strats[0]}」，{(1-q):.3f} 选择「{p2_strats[1]}」" if q is not None else "退化解",
                    "probabilities": [round(q, 4), round(1 - q, 4)] if q is not None else None,
                },
                "expected_payoffs": [round(exp_p1, 4), round(exp_p2, 4)] if exp_p1 is not None else None,
            },
            "formula_used": "p = (d2-c2)/(a2-b2-c2+d2), q = (d1-b1)/(a1-b1-c1+d1)",
            "note": (
                "混合策略均衡的含义：参与者按此概率分布随机选择策略，"
                "使对方在任何纯策略上的期望收益相等，从而对方没有偏离动机。"
            ),
        }

        # 检查纯策略均衡
        pure_check = False
        if p is not None and q is not None:
            if abs(p) < 1e-6 or abs(p - 1) < 1e-6 or abs(q) < 1e-6 or abs(q - 1) < 1e-6:
                pure_check = True
                result["mixed_equilibrium"]["note"] = "混合概率接近 0 或 1，实际为纯策略均衡"

        return json.dumps(result, ensure_ascii=False, indent=2)


# ── Tool 5: 占优策略分析 ───────────────────────────────────

class CheckDominanceTool(BaseTool):
    name: str = "check_dominance"
    description: str = (
        "识别博弈中的严格/弱占优策略和严格/弱劣策略。"
        "检查每个参与者是否有无论对方如何选择都更好的策略。"
    )
    args_schema: Type[BaseModel] = PayoffMatrixStr

    def _run(self, payoff_matrix: str) -> str:
        try:
            data = _parse_matrix(payoff_matrix)
            _validate_2player(data)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

        p1 = _p1_payoffs(data)
        p2 = _p2_payoffs(data)
        players = data["players"]
        p1_strats = data["strategies"][players[0]]
        p2_strats = data["strategies"][players[1]]

        rows, cols = len(p1), len(p1[0])

        def check_dominance_row(payoffs: list[list[float]], n_rows: int, n_cols: int,
                                strat_names: list[str]) -> list[dict]:
            """检查行玩家的占优关系。"""
            result = []
            for i in range(n_rows):
                strict_dom_count = 0
                weak_dom_count = 0
                for k in range(n_rows):
                    if i == k:
                        continue
                    strict_better = all(payoffs[i][j] > payoffs[k][j] for j in range(n_cols))
                    weak_better = all(payoffs[i][j] >= payoffs[k][j] for j in range(n_cols))
                    if strict_better:
                        strict_dom_count += 1
                    if weak_better:
                        weak_dom_count += 1

                entry = {"strategy": strat_names[i], "index": i}
                if strict_dom_count == n_rows - 1:
                    entry["status"] = "严格占优"
                    entry["detail"] = f"「{strat_names[i]}」严格优于所有其他策略"
                elif weak_dom_count == n_rows - 1:
                    entry["status"] = "弱占优"
                    entry["detail"] = f"「{strat_names[i]}」弱优于所有其他策略"
                elif strict_dom_count == 0 and weak_dom_count < n_rows - 1:
                    # 检查是否被占优
                    dominated_count = 0
                    for k in range(n_rows):
                        if i == k:
                            continue
                        if all(payoffs[k][j] > payoffs[i][j] for j in range(n_cols)):
                            dominated_count += 1
                    if dominated_count == n_rows - 1:
                        entry["status"] = "严格劣策略"
                        entry["detail"] = f"「{strat_names[i]}」严格劣于所有其他策略"
                    else:
                        for k in range(n_rows):
                            if i == k:
                                continue
                            if all(payoffs[k][j] >= payoffs[i][j] for j in range(n_cols)) and \
                               any(payoffs[k][j] > payoffs[i][j] for j in range(n_cols)):
                                entry["status"] = "弱劣策略"
                                entry["detail"] = f"「{strat_names[i]}」被「{strat_names[k]}」弱占优"
                                break
                        else:
                            entry["status"] = "无占优关系"
                            entry["detail"] = f"「{strat_names[i]}」既不被占优也不占优其他策略"
                else:
                    entry["status"] = "无占优关系"
                    entry["detail"] = f"「{strat_names[i]}」无简单占优关系"
                result.append(entry)
            return result

        p1_dominance = check_dominance_row(p1, rows, cols, p1_strats)
        p2_dominance = check_dominance_row(p2, cols, rows, p2_strats)

        result = {
            players[0]: p1_dominance,
            players[1]: p2_dominance,
            "can_iterated_elimination": any(
                d["status"] in ("严格劣策略", "弱劣策略")
                for p in [p1_dominance, p2_dominance] for d in p
            ),
            "summary": self._summarize(p1_dominance, p2_dominance, players),
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    def _summarize(self, p1_dom: list[dict], p2_dom: list[dict],
                   players: list[str]) -> str:
        lines = []
        for dom, name in [(p1_dom, players[0]), (p2_dom, players[1])]:
            entries = ", ".join(f"{d['strategy']}({d['status']})" for d in dom)
            lines.append(f"{name}: {entries}")
        return " | ".join(lines)


# ── Tool 6: Pareto 最优分析 ────────────────────────────────

class ParetoAnalysisTool(BaseTool):
    name: str = "pareto_analysis"
    description: str = (
        "分析收益矩阵的 Pareto 最优性。"
        "识别 Pareto 前沿面（不被任何其他结果 Pareto 占优的结果）。"
        "标记 Pareto 改进机会。"
    )
    args_schema: Type[BaseModel] = PayoffMatrixStr

    def _run(self, payoff_matrix: str) -> str:
        try:
            data = _parse_matrix(payoff_matrix)
            _validate_2player(data)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

        p1 = _p1_payoffs(data)
        p2 = _p2_payoffs(data)
        players = data["players"]
        p1_strats = data["strategies"][players[0]]
        p2_strats = data["strategies"][players[1]]

        rows, cols = len(p1), len(p1[0])

        # 收集所有结果
        outcomes = []
        for i in range(rows):
            for j in range(cols):
                outcomes.append({
                    "strategies": (p1_strats[i], p2_strats[j]),
                    "payoffs": (p1[i][j], p2[i][j]),
                    "coords": (i, j),
                })

        # Pareto 最优性检查
        pareto_frontier = []
        dominated = []

        for o in outcomes:
            is_dominated = False
            dominated_by = []
            for o2 in outcomes:
                if o is o2:
                    continue
                # o2 Pareto 占优 o：o2 所有收益 >= o 且至少一个严格 >
                p2_dom = (
                    o2["payoffs"][0] >= o["payoffs"][0] and
                    o2["payoffs"][1] >= o["payoffs"][1] and
                    (o2["payoffs"][0] > o["payoffs"][0] or o2["payoffs"][1] > o["payoffs"][1])
                )
                if p2_dom:
                    is_dominated = True
                    dominated_by.append(o2["strategies"])

            if is_dominated:
                dominated.append({
                    "strategies": o["strategies"],
                    "payoffs": o["payoffs"],
                    "dominated_by": dominated_by,
                })
            else:
                pareto_frontier.append({
                    "strategies": o["strategies"],
                    "payoffs": o["payoffs"],
                })

        # Pareto 改进路径
        improvements = []
        for i in range(rows):
            for j in range(cols):
                for k in range(rows):
                    for l in range(cols):
                        if (i, j) == (k, l):
                            continue
                        if (p1[k][l] >= p1[i][j] and p2[k][l] >= p2[i][j] and
                            (p1[k][l] > p1[i][j] or p2[k][l] > p2[i][j])):
                            improvements.append({
                                "from": {"strategies": (p1_strats[i], p2_strats[j]),
                                         "payoffs": (p1[i][j], p2[i][j])},
                                "to": {"strategies": (p1_strats[k], p2_strats[l]),
                                       "payoffs": (p1[k][l], p2[k][l])},
                            })

        result = {
            "pareto_frontier": pareto_frontier,
            "frontier_count": len(pareto_frontier),
            "dominated_outcomes": dominated,
            "dominated_count": len(dominated),
            "pareto_improvements": improvements[:10],  # 最多展示 10 条
            "summary": (
                f"Pareto 前沿面包含 {len(pareto_frontier)} 个结果，"
                f"{len(dominated)} 个被占优。"
            ),
        }
        return json.dumps(result, ensure_ascii=False, indent=2)


# ── 导出实例 ────────────────────────────────────────────────

build_payoff_matrix = BuildPayoffMatrixTool()
identify_game_type = IdentifyGameTypeTool()
solve_pure_nash = SolvePureNashTool()
solve_mixed_nash = SolveMixedNashTool()
check_dominance = CheckDominanceTool()
pareto_analysis = ParetoAnalysisTool()

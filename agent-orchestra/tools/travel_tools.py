"""
Travel Genius 工具模块
提供两个核心工具：search_places（灵感搜索）和 check_practicality（可行性验证）
"""

import json
import random
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type


# ── 输入 schema ──────────────────────────────────────────────

class SearchPlacesInput(BaseModel):
    interests: str = Field(
        ..., description="用户的旅行兴趣关键词，如 '艺术 潮流 小众'"
    )
    destination: str = Field(
        ..., description="目标城市或地区，如 '东京'"
    )


class CheckPracticalityInput(BaseModel):
    places_json: str = Field(
        ..., description='待验证的地点列表 JSON 字符串，格式为 [{"name":..., "type":..., "description":...}, ...]'
    )
    budget: str = Field(
        default="中等", description="预算等级：低 / 中等 / 高"
    )
    days: int = Field(
        default=5, description="旅行天数"
    )


# ── 模拟数据库 ───────────────────────────────────────────────

PLACE_DB = {
    "艺术": [
        {"name": "森美术馆", "type": "美术馆", "description": "六本木之丘52楼，东京最高美术馆，常设当代艺术大展"},
        {"name": "teamLab Borderless", "type": "数字艺术", "description": "无边界数字艺术博物馆，沉浸式光影体验"},
        {"name": "SCAI The Bathhouse", "type": "画廊", "description": "藏在百年澡堂里的前卫画廊，小众文艺打卡地"},
        {"name": "21_21 DESIGN SIGHT", "type": "设计", "description": "三宅一生发起的设计空间，由安藤忠雄操刀设计"},
    ],
    "潮流": [
        {"name": "下北泽", "type": "街区", "description": "古着店和独立咖啡馆的天堂，东京文艺青年聚集地"},
        {"name": "中目黑高架桥", "type": "商业街", "description": "废弃铁路改造的潮流商业空间，Blue Bottle在此"},
        {"name": "代官山蔦屋書店", "type": "书店", "description": "全球最美书店之一，生活美学提案空间"},
        {"name": "表参道 Hills", "type": "商业", "description": "安藤忠雄设计，表参道地标级潮流购物中心"},
    ],
    "小众": [
        {"name": "谷中银座商店街", "type": "老街", "description": "昭和风情商店街，黄昏时分的夕焼けだんだん（夕阳阶梯）绝美"},
        {"name": "Oedo Antique Market", "type": "市集", "description": "东京最大露天古董市集，每月第一和第三个周日"},
        {"name": "Ameya-Yokocho", "type": "市场", "description": "上野阿美横丁，海鲜小吃和庶民烟火气"},
        {"name": "井之头恩赐公园", "type": "公园", "description": "吉祥寺旁的赏樱胜地，可划船，周末有手工市集"},
    ],
    "美食": [
        {"name": "筑地场外市场", "type": "市场", "description": "东京厨房，海鲜盖饭和玉子烧的朝圣地"},
        {"name": "思い出横丁", "type": "居酒屋街", "description": "新宿西口的烟火小巷，60多家昭和居酒屋密集排列"},
        {"name": "Afuri 拉面", "type": "拉面", "description": "柚子盐拉面创始店，清爽系拉面代表"},
        {"name": "秋叶原电气街", "type": "街区", "description": "宅文化圣地，女仆咖啡和扭蛋机集中地"},
    ],
    "自然": [
        {"name": "高尾山", "type": "山", "description": "米其林三星绿色指南推荐，东京后花园，登顶可望富士山"},
        {"name": "明治神宫", "type": "神社", "description": "代代木的都市绿洲，原宿旁的宁静鸟居参道"},
        {"name": "目黑周边散步", "type": "街区", "description": "目黑川沿岸咖啡馆和独立书店散策路线"},
        {"name": "新宿御苑", "type": "庭园", "description": "都市中的英式/日式/法式混合庭园，四季皆美"},
    ],
}

# 地点类型到兴趣关键词的映射
TYPE_TO_INTEREST = {
    "美术馆": "艺术", "数字艺术": "艺术", "画廊": "艺术", "设计": "艺术",
    "街区": "潮流", "商业街": "潮流", "书店": "潮流", "商业": "潮流",
    "老街": "小众", "市集": "小众", "市场": "小众", "公园": "小众",
    "居酒屋街": "美食", "拉面": "美食",
    "山": "自然", "神社": "自然", "庭园": "自然",
}

# 预算到费用范围的映射
BUDGET_MAP = {
    "低": (100, 300),
    "中等": (300, 800),
    "高": (800, 2000),
}


# ── 工具实现 ─────────────────────────────────────────────────

class SearchPlacesTool(BaseTool):
    name: str = "search_places"
    description: str = (
        "根据用户兴趣和目标城市，搜索并返回一组旅行地点推荐。"
        "返回 JSON 数组，每项包含 name、type、description 字段。"
    )
    args_schema: Type[BaseModel] = SearchPlacesInput

    def _run(self, interests: str, destination: str) -> str:
        # 将用户兴趣拆分为关键词
        keywords = [k.strip() for k in interests.replace("，", " ").split() if k.strip()]

        results = []
        for kw in keywords:
            for category, places in PLACE_DB.items():
                # 模糊匹配：关键词包含在类别名中，或类别名包含在关键词中
                if kw in category or category in kw:
                    results.extend(places)

        # 如果没有匹配到，随机从所有类别中抽取
        if not results:
            all_places = [p for places in PLACE_DB.values() for p in places]
            results = random.sample(all_places, min(6, len(all_places)))

        # 去重
        seen = set()
        unique = []
        for p in results:
            if p["name"] not in seen:
                seen.add(p["name"])
                unique.append(p)

        # 为每个地点添加模拟距离和费用
        enriched = []
        for p in unique[:8]:  # 最多返回 8 个
            entry = {
                **p,
                "city": destination,
                "distance_km": round(random.uniform(1, 30), 1),
                "estimated_cost_cny": random.randint(50, 500),
            }
            enriched.append(entry)

        return json.dumps(enriched, ensure_ascii=False, indent=2)


class CheckPracticalityTool(BaseTool):
    name: str = "check_practicality"
    description: str = (
        "验证一组旅行地点的可行性（距离、花费、开放状态），"
        "返回过滤后的结果及每个地点的实用点评。"
    )
    args_schema: Type[BaseModel] = CheckPracticalityInput

    def _run(self, places_json: str, budget: str = "中等", days: int = 5) -> str:
        try:
            places = json.loads(places_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "输入的 JSON 格式有误，请检查"}, ensure_ascii=False)

        budget_range = BUDGET_MAP.get(budget, BUDGET_MAP["中等"])
        daily_budget = budget_range[1] / max(days, 1)

        result = {"validated": [], "filtered_out": []}

        for place in places:
            cost = place.get("estimated_cost_cny", 200)
            dist = place.get("distance_km", 10)
            name = place.get("name", "未知")

            # 过滤逻辑
            reasons = []
            if cost > daily_budget * 1.5:
                reasons.append(f"费用 ¥{cost} 超出每日预算 ¥{daily_budget:.0f}")
            if dist > 25:
                reasons.append(f"距离 {dist}km 太远，通勤不划算")

            # 模拟开放状态（90% 概率开放）
            is_open = random.random() > 0.1
            if not is_open:
                reasons.append("当前因维护/闭馆暂不开放")

            # 生成毒舌点评
            snarky_comment = _generate_snarky_comment(place, cost, dist, is_open)

            entry = {
                "name": name,
                "type": place.get("type", ""),
                "description": place.get("description", ""),
                "estimated_cost_cny": cost,
                "distance_km": dist,
                "is_open": is_open,
                "snarky_comment": snarky_comment,
            }

            if reasons:
                entry["rejection_reasons"] = reasons
                result["filtered_out"].append(entry)
            else:
                result["validated"].append(entry)

        # 限制通过的数量为 days+1 个（每天一个 + 一个备选）
        max_pass = min(len(result["validated"]), days + 1)
        result["validated"] = result["validated"][:max_pass]
        result["summary"] = (
            f"共验证 {len(places)} 个地点：{len(result['validated'])} 个通过，"
            f"{len(result['filtered_out'])} 个被淘汰。"
        )

        return json.dumps(result, ensure_ascii=False, indent=2)


def _generate_snarky_comment(place: dict, cost: float, dist: float, is_open: bool) -> str:
    """根据地点信息生成带毒舌风格的点评"""
    name = place.get("name", "这地方")
    ptype = place.get("type", "")
    desc = place.get("description", "")

    templates_open = [
        f"{name}？说实话，{desc}——但周末人多到你怀疑人生，建议工作日去。",
        f"行吧，{name}确实值得去。{desc}。就是周边吃饭贵，记得自带干粮（开玩笑的）。",
        f"{name}，{ptype}类的扛把子。{desc}。拍照发朋友圈至少能骗200个赞。",
        f"终于有个靠谱的了——{name}。{desc}。我本地人都会偶尔去，说明是真的好。",
        f"{name}：{desc}。唯一的缺点是你会拍太多照片导致手机没电。",
    ]

    templates_closed = [
        f"{name}现在关着呢，别白跑一趟。{desc}——等它开了再去吧。",
        f"哎呀，{name}当前不开放。{desc}。省下的钱去旁边吃碗拉面也挺好。",
    ]

    templates_far = [
        f"{name}嘛……{desc}。但 {dist}km 的距离，你确定不是来拉练的？",
        f"如果你不介意单程 {dist}km 的话——{name}还行吧。{desc}。",
    ]

    templates_expensive = [
        f"{name}，{desc}。花 ¥{cost}？我本地人觉得有点宰游客了。",
        f"{name}确实不错，{desc}。但 ¥{cost} 的价格让我这个本地人都肉疼。",
    ]

    if not is_open:
        return random.choice(templates_closed)
    if dist > 20:
        return random.choice(templates_far)
    if cost > 400:
        return random.choice(templates_expensive)
    return random.choice(templates_open)


# ── 导出 ─────────────────────────────────────────────────────

search_places = SearchPlacesTool()
check_practicality = CheckPracticalityTool()

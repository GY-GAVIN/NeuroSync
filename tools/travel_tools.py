"""
Travel Genius 工具模块（真实 API 版本）
提供两个核心工具：search_places（灵感搜索）和 check_practicality（可行性验证）

集成的外部 API：
  - SerpAPI Google Maps：根据兴趣关键词搜索真实地点
  - OpenWeatherMap：获取当前天气，辅助判断户外活动可行性
  - geopy：地理编码 + 距离计算
"""

import json
import os
import random
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

# ── API 配置 ──────────────────────────────────────────────────

SERPAPI_KEY = os.getenv("SERPAPI_API_KEY", "")
OWM_KEY = os.getenv("OPENWEATHERMAP_API_KEY", "")

API_TIMEOUT = 8  # 秒，所有外部调用统一超时


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
        ..., description='待验证的地点列表 JSON 字符串，格式为 [{"name":..., "type":..., "description":..., "city":...}, ...]'
    )
    budget: str = Field(
        default="中等", description="预算等级：低 / 中等 / 高"
    )
    days: int = Field(
        default=5, description="旅行天数"
    )


# ── 预算映射 ─────────────────────────────────────────────────

BUDGET_MAP = {
    "低": (100, 300),
    "中等": (300, 800),
    "高": (800, 2000),
}

# ── 备用模拟数据（API 不可用时降级使用）────────────────────────

FALLBACK_PLACES = {
    "艺术": [
        {"name": "森美术馆", "type": "美术馆", "description": "六本木之丘52楼，东京最高美术馆"},
        {"name": "teamLab Borderless", "type": "数字艺术", "description": "无边界数字艺术博物馆"},
        {"name": "SCAI The Bathhouse", "type": "画廊", "description": "藏在百年澡堂里的前卫画廊"},
    ],
    "潮流": [
        {"name": "下北泽", "type": "街区", "description": "古着店和独立咖啡馆的天堂"},
        {"name": "中目黑高架桥", "type": "商业街", "description": "废弃铁路改造的潮流商业空间"},
        {"name": "代官山蔦屋書店", "type": "书店", "description": "全球最美书店之一"},
    ],
    "小众": [
        {"name": "谷中银座商店街", "type": "老街", "description": "昭和风情商店街"},
        {"name": "Ameya-Yokocho", "type": "市场", "description": "上野阿美横丁，海鲜小吃"},
    ],
    "美食": [
        {"name": "筑地场外市场", "type": "市场", "description": "东京厨房，海鲜盖饭朝圣地"},
        {"name": "思い出横丁", "type": "居酒屋街", "description": "新宿西口的烟火小巷"},
    ],
    "自然": [
        {"name": "高尾山", "type": "山", "description": "米其林三星绿色指南推荐"},
        {"name": "明治神宫", "type": "神社", "description": "代代木的都市绿洲"},
    ],
}


# ── 辅助函数 ─────────────────────────────────────────────────

def _serpapi_search(query: str) -> list[dict]:
    """调用 SerpAPI Google Maps 搜索，返回地点列表。"""
    if not SERPAPI_KEY:
        raise ValueError("SERPAPI_API_KEY 未配置")

    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_maps",
        "q": query,
        "type": "search",
        "api_key": SERPAPI_KEY,
        "hl": "zh-cn",
        "num": 10,
    }
    resp = requests.get(url, params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data.get("local_results", [])


def _owm_current_weather(city: str) -> dict | None:
    """调用 OpenWeatherMap 获取当前天气，失败返回 None。"""
    if not OWM_KEY:
        raise ValueError("OPENWEATHERMAP_API_KEY 未配置")

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OWM_KEY,
        "units": "metric",
        "lang": "zh_cn",
    }
    resp = requests.get(url, params=params, timeout=API_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _geocode_address(address: str) -> tuple[float, float] | None:
    """用 geopy 的 Nominatim 将地址转为坐标，失败返回 None。"""
    from geopy.geocoders import Nominatim

    geolocator = Nominatim(user_agent="neurosync_travel_genius", timeout=API_TIMEOUT)
    location = geolocator.geocode(address)
    if location:
        return (location.latitude, location.longitude)
    return None


def _calc_distance_km(
    origin: tuple[float, float], dest: tuple[float, float]
) -> float:
    """用 geopy 计算两点之间的大圆距离（km）。"""
    from geopy.distance import geodesic

    return round(geodesic(origin, dest).km, 1)


def _weather_advisory(weather: dict) -> dict:
    """根据天气数据生成户外活动建议。"""
    main = weather.get("weather", [{}])[0].get("main", "").lower()
    desc = weather.get("weather", [{}])[0].get("description", "")
    temp = weather.get("main", {}).get("temp", 20)
    rain = weather.get("rain", {}).get("1h", 0)

    outdoor_ok = True
    reason = f"当前天气：{desc}，气温 {temp}°C"

    if main in ("rain", "thunderstorm", "snow", "drizzle"):
        outdoor_ok = False
        reason += "。不建议户外活动"
    elif temp > 38 or temp < -5:
        outdoor_ok = False
        reason += "。气温极端，不建议长时间户外"
    elif rain > 5:
        outdoor_ok = False
        reason += f"。过去一小时降雨 {rain}mm，注意防雨"

    return {"outdoor_ok": outdoor_ok, "reason": reason, "temp": temp, "description": desc}


# ── 工具实现 ─────────────────────────────────────────────────

class SearchPlacesTool(BaseTool):
    name: str = "search_places"
    description: str = (
        "根据用户兴趣和目标城市，通过 Google Maps 搜索并返回一组真实旅行地点推荐。"
        "返回 JSON 数组，每项包含 name、type、description、rating、address 字段。"
    )
    args_schema: Type[BaseModel] = SearchPlacesInput

    def _run(self, interests: str, destination: str) -> str:
        keywords = [k.strip() for k in interests.replace("，", " ").split() if k.strip()]
        all_results = []
        api_ok = False

        # ── 尝试 SerpAPI ─────────────────────────────────────
        for kw in keywords:
            query = f"{kw} {destination}"
            try:
                raw = _serpapi_search(query)
                for place in raw:
                    entry = {
                        "name": place.get("title", "未知地点"),
                        "type": place.get("type", kw),
                        "description": place.get("snippet", place.get("description", "")),
                        "rating": place.get("rating"),
                        "address": place.get("address", ""),
                        "latitude": place.get("gps_coordinates", {}).get("latitude"),
                        "longitude": place.get("gps_coordinates", {}).get("longitude"),
                        "city": destination,
                    }
                    all_results.append(entry)
                api_ok = True
            except requests.Timeout:
                continue
            except requests.RequestException:
                continue
            except ValueError:
                # API key 未配置，直接跳出
                break

        # ── 去重 ─────────────────────────────────────────────
        seen = set()
        unique = []
        for p in all_results:
            key = p["name"]
            if key not in seen:
                seen.add(key)
                unique.append(p)

        # ── 如果 API 全部失败，降级到模拟数据 ────────────────
        if not unique:
            fallback_msg = (
                "⚠️ SerpAPI 暂时不可用（未配置或请求失败），"
                "以下为备用推荐数据，仅供参考。\n"
            )
            for kw in keywords:
                for category, places in FALLBACK_PLACES.items():
                    if kw in category or category in kw:
                        for p in places:
                            unique.append({**p, "city": destination})
            if not unique:
                all_places = [p for ps in FALLBACK_PLACES.values() for p in ps]
                sampled = random.sample(all_places, min(6, len(all_places)))
                for p in sampled:
                    unique.append({**p, "city": destination})
        else:
            fallback_msg = ""

        # 限制返回数量
        unique = unique[:8]

        return fallback_msg + json.dumps(unique, ensure_ascii=False, indent=2)


class CheckPracticalityTool(BaseTool):
    name: str = "check_practicality"
    description: str = (
        "验证一组旅行地点的可行性：通过 OpenWeatherMap 获取天气判断是否适合户外，"
        "通过 geopy 计算酒店到景点的距离。返回过滤后的结果及实用点评。"
    )
    args_schema: Type[BaseModel] = CheckPracticalityInput

    def _run(self, places_json: str, budget: str = "中等", days: int = 5) -> str:
        try:
            places = json.loads(places_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "输入的 JSON 格式有误，请检查"}, ensure_ascii=False)

        budget_range = BUDGET_MAP.get(budget, BUDGET_MAP["中等"])
        daily_budget = budget_range[1] / max(days, 1)

        # ── 获取天气（一次，按城市） ─────────────────────────
        city = places[0].get("city", "") if places else ""
        weather_info = None
        weather_note = ""
        try:
            weather_data = _owm_current_weather(city)
            weather_info = _weather_advisory(weather_data)
            weather_note = weather_info["reason"]
        except (requests.Timeout, requests.RequestException):
            weather_note = "⚠️ 暂时无法获取天气数据，已跳过天气验证。"
        except ValueError:
            weather_note = "⚠️ OpenWeatherMap API Key 未配置，已跳过天气验证。"

        # ── 获取酒店坐标（用于距离计算） ────────────────────
        hotel_coords = None
        if city:
            try:
                hotel_coords = _geocode_address(city + " 市中心")
            except Exception:
                pass

        result = {
            "validated": [],
            "filtered_out": [],
            "weather": weather_note,
        }

        for place in places:
            name = place.get("name", "未知")
            cost = place.get("estimated_cost_cny", 200)
            ptype = place.get("type", "")
            lat = place.get("latitude")
            lon = place.get("longitude")

            reasons = []

            # 费用检查
            if cost > daily_budget * 1.5:
                reasons.append(f"费用 ¥{cost} 超出每日预算 ¥{daily_budget:.0f}")

            # 距离检查（真实计算）
            distance_km = place.get("distance_km")
            if lat and lon and hotel_coords:
                try:
                    distance_km = _calc_distance_km(hotel_coords, (lat, lon))
                except Exception:
                    pass  # 保留原值

            if distance_km and distance_km > 25:
                reasons.append(f"距离 {distance_km}km 太远，通勤不划算")

            # 天气检查（户外类型才检查）
            outdoor_types = {"山", "公园", "神社", "庭园", "街区", "老街", "市集", "市场"}
            if weather_info and ptype in outdoor_types and not weather_info["outdoor_ok"]:
                reasons.append(f"当前天气不适合户外活动：{weather_info['description']}")

            # 生成点评
            snarky_comment = _generate_snarky_comment(place, cost, distance_km or 10, weather_info)

            entry = {
                "name": name,
                "type": ptype,
                "description": place.get("description", ""),
                "estimated_cost_cny": cost,
                "distance_km": distance_km or "未知",
                "weather": weather_note,
                "snarky_comment": snarky_comment,
            }

            if reasons:
                entry["rejection_reasons"] = reasons
                result["filtered_out"].append(entry)
            else:
                result["validated"].append(entry)

        max_pass = min(len(result["validated"]), days + 1)
        result["validated"] = result["validated"][:max_pass]
        result["summary"] = (
            f"共验证 {len(places)} 个地点：{len(result['validated'])} 个通过，"
            f"{len(result['filtered_out'])} 个被淘汰。"
        )

        return json.dumps(result, ensure_ascii=False, indent=2)


def _generate_snarky_comment(
    place: dict, cost: float, dist: float, weather_info: dict | None
) -> str:
    """根据地点信息生成带毒舌风格的点评。"""
    name = place.get("name", "这地方")
    ptype = place.get("type", "")
    desc = place.get("description", "")

    weather_str = ""
    if weather_info:
        weather_str = f"。天气方面，{weather_info['reason']}"

    templates_open = [
        f"{name}？说实话，{desc}——但周末人多到你怀疑人生，建议工作日去{weather_str}。",
        f"行吧，{name}确实值得去。{desc}。就是周边吃饭贵，记得自带干粮（开玩笑的）{weather_str}。",
        f"{name}，{ptype}类的扛把子。{desc}。拍照发朋友圈至少能骗200个赞{weather_str}。",
        f"终于有个靠谱的了——{name}。{desc}。我本地人都会偶尔去，说明是真的好{weather_str}。",
    ]

    templates_far = [
        f"{name}嘛……{desc}。但 {dist}km 的距离，你确定不是来拉练的？",
        f"如果你不介意单程 {dist}km 的话——{name}还行吧。{desc}。",
    ]

    templates_expensive = [
        f"{name}，{desc}。花 ¥{cost}？我本地人觉得有点宰游客了。",
        f"{name}确实不错，{desc}。但 ¥{cost} 的价格让我这个本地人都肉疼。",
    ]

    if isinstance(dist, (int, float)) and dist > 20:
        return random.choice(templates_far)
    if cost > 400:
        return random.choice(templates_expensive)
    return random.choice(templates_open)


# ── 导出 ─────────────────────────────────────────────────────

search_places = SearchPlacesTool()
check_practicality = CheckPracticalityTool()

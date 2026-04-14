#!/usr/bin/env python3
"""Nutrition tracking, meal logging, and dietary analysis — MEOK AI Labs."""
import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

import json
from datetime import datetime, timezone
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)


def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now - t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT:
        return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now)
    return None


# In-memory meal log keyed by user session
_meal_log = defaultdict(list)

# Nutrition database (per 100g serving)
_FOODS = {
    "chicken breast": {"calories": 165, "protein": 31, "carbs": 0, "fat": 3.6, "fiber": 0, "category": "protein"},
    "salmon": {"calories": 208, "protein": 20, "carbs": 0, "fat": 13, "fiber": 0, "category": "protein"},
    "egg": {"calories": 155, "protein": 13, "carbs": 1.1, "fat": 11, "fiber": 0, "category": "protein"},
    "rice": {"calories": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4, "category": "grain"},
    "brown rice": {"calories": 123, "protein": 2.7, "carbs": 26, "fat": 1, "fiber": 1.8, "category": "grain"},
    "pasta": {"calories": 131, "protein": 5, "carbs": 25, "fat": 1.1, "fiber": 1.8, "category": "grain"},
    "bread": {"calories": 265, "protein": 9, "carbs": 49, "fat": 3.2, "fiber": 2.7, "category": "grain"},
    "oats": {"calories": 389, "protein": 17, "carbs": 66, "fat": 7, "fiber": 11, "category": "grain"},
    "banana": {"calories": 89, "protein": 1.1, "carbs": 23, "fat": 0.3, "fiber": 2.6, "category": "fruit"},
    "apple": {"calories": 52, "protein": 0.3, "carbs": 14, "fat": 0.2, "fiber": 2.4, "category": "fruit"},
    "orange": {"calories": 47, "protein": 0.9, "carbs": 12, "fat": 0.1, "fiber": 2.4, "category": "fruit"},
    "strawberry": {"calories": 32, "protein": 0.7, "carbs": 7.7, "fat": 0.3, "fiber": 2, "category": "fruit"},
    "broccoli": {"calories": 34, "protein": 2.8, "carbs": 7, "fat": 0.4, "fiber": 2.6, "category": "vegetable"},
    "spinach": {"calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "fiber": 2.2, "category": "vegetable"},
    "carrot": {"calories": 41, "protein": 0.9, "carbs": 10, "fat": 0.2, "fiber": 2.8, "category": "vegetable"},
    "sweet potato": {"calories": 86, "protein": 1.6, "carbs": 20, "fat": 0.1, "fiber": 3, "category": "vegetable"},
    "avocado": {"calories": 160, "protein": 2, "carbs": 9, "fat": 15, "fiber": 7, "category": "fat"},
    "olive oil": {"calories": 884, "protein": 0, "carbs": 0, "fat": 100, "fiber": 0, "category": "fat"},
    "almonds": {"calories": 579, "protein": 21, "carbs": 22, "fat": 50, "fiber": 12, "category": "fat"},
    "milk": {"calories": 42, "protein": 3.4, "carbs": 5, "fat": 1, "fiber": 0, "category": "dairy"},
    "yogurt": {"calories": 59, "protein": 10, "carbs": 3.6, "fat": 0.7, "fiber": 0, "category": "dairy"},
    "cheese": {"calories": 402, "protein": 25, "carbs": 1.3, "fat": 33, "fiber": 0, "category": "dairy"},
    "tofu": {"calories": 76, "protein": 8, "carbs": 1.9, "fat": 4.8, "fiber": 0.3, "category": "protein"},
    "lentils": {"calories": 116, "protein": 9, "carbs": 20, "fat": 0.4, "fiber": 8, "category": "legume"},
    "chickpeas": {"calories": 164, "protein": 8.9, "carbs": 27, "fat": 2.6, "fiber": 8, "category": "legume"},
}


mcp = FastMCP("nutrition-tracker-ai-mcp", instructions="Nutrition tracking and dietary analysis by MEOK AI Labs.")


@mcp.tool(name="log_meal")
async def log_meal(user_id: str, foods: list, servings_grams: list = None, meal_type: str = "snack", api_key: str = "") -> dict:
    """Log a meal with foods and serving sizes. Foods are matched against built-in database."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(api_key or "anon"):
        return err

    if not foods:
        return {"error": "No foods provided."}

    if servings_grams is None:
        servings_grams = [100] * len(foods)
    while len(servings_grams) < len(foods):
        servings_grams.append(100)

    items = []
    total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
    unrecognized = []

    for food_name, grams in zip(foods, servings_grams):
        key = food_name.lower().strip()
        if key in _FOODS:
            info = _FOODS[key]
            ratio = grams / 100.0
            item = {
                "food": food_name,
                "grams": grams,
                "calories": round(info["calories"] * ratio, 1),
                "protein": round(info["protein"] * ratio, 1),
                "carbs": round(info["carbs"] * ratio, 1),
                "fat": round(info["fat"] * ratio, 1),
                "fiber": round(info["fiber"] * ratio, 1),
                "category": info["category"],
            }
            for k in total:
                total[k] += item[k]
            items.append(item)
        else:
            unrecognized.append(food_name)

    for k in total:
        total[k] = round(total[k], 1)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "meal_type": meal_type,
        "items": items,
        "total": total,
    }
    _meal_log[user_id].append(entry)

    result = {
        "status": "logged",
        "meal_type": meal_type,
        "items_logged": len(items),
        "total_nutrition": total,
        "timestamp": entry["timestamp"],
    }
    if unrecognized:
        result["unrecognized_foods"] = unrecognized
        result["note"] = "Unrecognized foods were skipped. Use get_calorie_estimate for custom foods."
    return result


@mcp.tool(name="get_daily_summary")
async def get_daily_summary(user_id: str, api_key: str = "") -> dict:
    """Get a summary of all meals logged today for a user."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(api_key or "anon"):
        return err

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    meals = [m for m in _meal_log.get(user_id, []) if m["timestamp"].startswith(today)]

    daily_total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
    meal_breakdown = []

    for meal in meals:
        for k in daily_total:
            daily_total[k] += meal["total"].get(k, 0)
        meal_breakdown.append({
            "meal_type": meal["meal_type"],
            "time": meal["timestamp"],
            "calories": meal["total"]["calories"],
            "items": len(meal["items"]),
        })

    for k in daily_total:
        daily_total[k] = round(daily_total[k], 1)

    # Macro percentages
    total_cal = max(daily_total["calories"], 1)
    macro_pct = {
        "protein_pct": round(daily_total["protein"] * 4 / total_cal * 100, 1),
        "carbs_pct": round(daily_total["carbs"] * 4 / total_cal * 100, 1),
        "fat_pct": round(daily_total["fat"] * 9 / total_cal * 100, 1),
    }

    return {
        "user_id": user_id,
        "date": today,
        "meals_logged": len(meals),
        "total_nutrition": daily_total,
        "macro_percentages": macro_pct,
        "meal_breakdown": meal_breakdown,
    }


@mcp.tool(name="check_nutrient_balance")
async def check_nutrient_balance(user_id: str, weight_kg: float = 70, goal: str = "maintain", api_key: str = "") -> dict:
    """Check if today's nutrition is balanced against recommended targets."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(api_key or "anon"):
        return err

    goal_l = goal.lower()
    if "loss" in goal_l or "cut" in goal_l:
        cal_target = weight_kg * 28
        protein_target = weight_kg * 2.0
    elif "gain" in goal_l or "bulk" in goal_l or "muscle" in goal_l:
        cal_target = weight_kg * 38
        protein_target = weight_kg * 2.2
    else:
        cal_target = weight_kg * 33
        protein_target = weight_kg * 1.8

    carb_target = cal_target * 0.45 / 4
    fat_target = cal_target * 0.30 / 9
    fiber_target = 30

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    meals = [m for m in _meal_log.get(user_id, []) if m["timestamp"].startswith(today)]
    actual = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
    for meal in meals:
        for k in actual:
            actual[k] += meal["total"].get(k, 0)

    targets = {"calories": round(cal_target), "protein": round(protein_target), "carbs": round(carb_target), "fat": round(fat_target), "fiber": fiber_target}
    balance = {}
    warnings = []
    for k in targets:
        pct = round(actual[k] / max(targets[k], 1) * 100, 1)
        balance[k] = {"actual": round(actual[k], 1), "target": targets[k], "percent_of_target": pct}
        if pct > 120:
            warnings.append(f"{k} is {pct}% of target - consider reducing")
        elif pct < 50 and meals:
            warnings.append(f"{k} is only {pct}% of target - consider increasing")

    return {
        "user_id": user_id,
        "goal": goal,
        "weight_kg": weight_kg,
        "balance": balance,
        "warnings": warnings,
        "meals_today": len(meals),
        "overall_status": "on_track" if not warnings else "needs_adjustment",
    }


@mcp.tool(name="suggest_foods")
async def suggest_foods(nutrient: str = "protein", category: str = "", limit: int = 10, api_key: str = "") -> dict:
    """Suggest foods high in a specific nutrient, optionally filtered by category."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(api_key or "anon"):
        return err

    valid_nutrients = ["calories", "protein", "carbs", "fat", "fiber"]
    nutrient = nutrient.lower().strip()
    if nutrient not in valid_nutrients:
        return {"error": f"Invalid nutrient. Choose from: {valid_nutrients}"}

    foods = []
    for name, info in _FOODS.items():
        if category and info["category"] != category.lower().strip():
            continue
        foods.append({"food": name, "per_100g": info[nutrient], "category": info["category"], "calories": info["calories"]})

    foods.sort(key=lambda x: x["per_100g"], reverse=True)
    foods = foods[:limit]

    categories = sorted(set(info["category"] for info in _FOODS.values()))

    return {
        "nutrient": nutrient,
        "category_filter": category or "all",
        "suggestions": foods,
        "total_results": len(foods),
        "available_categories": categories,
    }


@mcp.tool(name="get_calorie_estimate")
async def get_calorie_estimate(food_description: str, grams: float = 100, api_key: str = "") -> dict:
    """Estimate calories for a food item. Matches against database or estimates from description."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
    if err := _rl(api_key or "anon"):
        return err

    key = food_description.lower().strip()

    # Direct match
    if key in _FOODS:
        info = _FOODS[key]
        ratio = grams / 100.0
        return {
            "food": food_description,
            "grams": grams,
            "calories": round(info["calories"] * ratio, 1),
            "protein": round(info["protein"] * ratio, 1),
            "carbs": round(info["carbs"] * ratio, 1),
            "fat": round(info["fat"] * ratio, 1),
            "fiber": round(info["fiber"] * ratio, 1),
            "match": "exact",
            "confidence": 0.95,
        }

    # Partial match
    partial = [(name, info) for name, info in _FOODS.items() if key in name or name in key]
    if partial:
        name, info = partial[0]
        ratio = grams / 100.0
        return {
            "food": food_description,
            "matched_to": name,
            "grams": grams,
            "calories": round(info["calories"] * ratio, 1),
            "protein": round(info["protein"] * ratio, 1),
            "carbs": round(info["carbs"] * ratio, 1),
            "fat": round(info["fat"] * ratio, 1),
            "fiber": round(info["fiber"] * ratio, 1),
            "match": "partial",
            "confidence": 0.7,
        }

    # Category-based estimate
    category_avg = defaultdict(lambda: {"calories": 0, "count": 0})
    for info in _FOODS.values():
        category_avg[info["category"]]["calories"] += info["calories"]
        category_avg[info["category"]]["count"] += 1

    avg_cal = sum(info["calories"] for info in _FOODS.values()) / max(len(_FOODS), 1)
    ratio = grams / 100.0

    return {
        "food": food_description,
        "grams": grams,
        "calories": round(avg_cal * ratio, 1),
        "match": "estimated",
        "confidence": 0.3,
        "note": f"No match found for '{food_description}'. Using average estimate. Known foods: {sorted(_FOODS.keys())[:10]}",
    }


if __name__ == "__main__":
    mcp.run()

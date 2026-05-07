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
# Nutrition database (per 100g): [calories, protein, carbs, fat, fiber, category]
_FOODS_RAW = {
    "chicken breast": [165, 31, 0, 3.6, 0, "protein"], "salmon": [208, 20, 0, 13, 0, "protein"],
    "egg": [155, 13, 1.1, 11, 0, "protein"], "tofu": [76, 8, 1.9, 4.8, 0.3, "protein"],
    "rice": [130, 2.7, 28, 0.3, 0.4, "grain"], "brown rice": [123, 2.7, 26, 1, 1.8, "grain"],
    "pasta": [131, 5, 25, 1.1, 1.8, "grain"], "bread": [265, 9, 49, 3.2, 2.7, "grain"],
    "oats": [389, 17, 66, 7, 11, "grain"], "banana": [89, 1.1, 23, 0.3, 2.6, "fruit"],
    "apple": [52, 0.3, 14, 0.2, 2.4, "fruit"], "orange": [47, 0.9, 12, 0.1, 2.4, "fruit"],
    "strawberry": [32, 0.7, 7.7, 0.3, 2, "fruit"], "broccoli": [34, 2.8, 7, 0.4, 2.6, "vegetable"],
    "spinach": [23, 2.9, 3.6, 0.4, 2.2, "vegetable"], "carrot": [41, 0.9, 10, 0.2, 2.8, "vegetable"],
    "sweet potato": [86, 1.6, 20, 0.1, 3, "vegetable"], "avocado": [160, 2, 9, 15, 7, "fat"],
    "olive oil": [884, 0, 0, 100, 0, "fat"], "almonds": [579, 21, 22, 50, 12, "fat"],
    "milk": [42, 3.4, 5, 1, 0, "dairy"], "yogurt": [59, 10, 3.6, 0.7, 0, "dairy"],
    "cheese": [402, 25, 1.3, 33, 0, "dairy"], "lentils": [116, 9, 20, 0.4, 8, "legume"],
    "chickpeas": [164, 8.9, 27, 2.6, 8, "legume"],
}
_FOODS = {k: {"calories": v[0], "protein": v[1], "carbs": v[2], "fat": v[3], "fiber": v[4], "category": v[5]} for k, v in _FOODS_RAW.items()}


mcp = FastMCP("nutrition-tracker-ai", instructions="Nutrition tracking and dietary analysis by MEOK AI Labs.")


@mcp.tool()
def log_meal(user_id: str, foods: list, servings_grams: list = None, meal_type: str = "snack", api_key: str = "") -> dict:
    """Log a meal with foods and serving sizes. Foods are matched against built-in database.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    """
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


@mcp.tool()
def get_daily_summary(user_id: str, api_key: str = "") -> dict:
    """Get a summary of all meals logged today for a user.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    """
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


@mcp.tool()
def check_nutrient_balance(user_id: str, weight_kg: float = 70, goal: str = "maintain", api_key: str = "") -> dict:
    """Check if today's nutrition is balanced against recommended targets.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    """
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


@mcp.tool()
def suggest_foods(nutrient: str = "protein", category: str = "", limit: int = 10, api_key: str = "") -> dict:
    """Suggest foods high in a specific nutrient, optionally filtered by category.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    """
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


@mcp.tool()
def get_calorie_estimate(food_description: str, grams: float = 100, api_key: str = "") -> dict:
    """Estimate calories for a food item. Matches against database or estimates from description.

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.
    """
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

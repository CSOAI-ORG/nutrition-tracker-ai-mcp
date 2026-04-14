#!/usr/bin/env python3

import sys, os
sys.path.insert(0, os.path.expanduser('~/clawd/meok-labs-engine/shared'))
from auth_middleware import check_access

from mcp.server.fastmcp import FastMCP
import json
mcp = FastMCP("nutrition-tracker-ai-mcp")
@mcp.tool(name="macro_calculator")
async def macro_calculator(weight_kg: float, goal: str, api_key: str = "") -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    protein = weight_kg * (2.0 if "muscle" in goal.lower() else 1.6)
    calories = weight_kg * (30 if "loss" in goal.lower() else 35)
    return {"calories": round(calories), "protein_g": round(protein), "carbs_g": round(calories*0.4/4), "fat_g": round(calories*0.3/9)}
@mcp.tool(name="meal_balance_score")
async def meal_balance_score(meal: dict, api_key: str = "") -> str:
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return {"error": msg, "upgrade_url": "https://meok.ai/pricing"}

    score = min(100, meal.get("protein_g", 0) * 2 + meal.get("vegetables", 0) * 10)
    return {"score": score, "rating": "Excellent" if score > 80 else "Good" if score > 50 else "Poor"}
if __name__ == "__main__":
    mcp.run()

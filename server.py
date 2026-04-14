#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import json
mcp = FastMCP("nutrition-tracker-ai-mcp")
@mcp.tool(name="macro_calculator")
async def macro_calculator(weight_kg: float, goal: str) -> str:
    protein = weight_kg * (2.0 if "muscle" in goal.lower() else 1.6)
    calories = weight_kg * (30 if "loss" in goal.lower() else 35)
    return json.dumps({"calories": round(calories), "protein_g": round(protein), "carbs_g": round(calories*0.4/4), "fat_g": round(calories*0.3/9)})
@mcp.tool(name="meal_balance_score")
async def meal_balance_score(meal: dict) -> str:
    score = min(100, meal.get("protein_g", 0) * 2 + meal.get("vegetables", 0) * 10)
    return json.dumps({"score": score, "rating": "Excellent" if score > 80 else "Good" if score > 50 else "Poor"})
if __name__ == "__main__":
    mcp.run()

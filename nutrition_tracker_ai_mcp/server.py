from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nutrition-tracker")

FOOD_LOG = []

@mcp.tool()
def log_food(name: str, calories: float, protein: float = 0, carbs: float = 0, fat: float = 0) -> dict:
    """Log a food item."""
    item = {"name": name, "calories": calories, "protein": protein, "carbs": carbs, "fat": fat}
    FOOD_LOG.append(item)
    return {"logged": item, "total_items": len(FOOD_LOG)}

@mcp.tool()
def get_daily_summary() -> dict:
    """Get daily nutrition summary."""
    totals = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    for item in FOOD_LOG:
        for k in totals:
            totals[k] += item[k]
    return {"totals": {k: round(v, 1) for k, v in totals.items()}, "items": len(FOOD_LOG)}

@mcp.tool()
def compare_to_targets(target_calories: float, target_protein: float, target_carbs: float, target_fat: float) -> dict:
    """Compare intake to targets."""
    summary = get_daily_summary()
    t = summary["totals"]
    comparison = {}
    for key, target in [("calories", target_calories), ("protein", target_protein), ("carbs", target_carbs), ("fat", target_fat)]:
        diff = t[key] - target
        comparison[key] = {
            "consumed": t[key],
            "target": target,
            "difference": round(diff, 1),
            "status": "over" if diff > 0 else "under" if diff < 0 else "on_target",
        }
    return {"comparison": comparison}

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()

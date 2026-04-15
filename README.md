# Nutrition Tracker AI

> By [MEOK AI Labs](https://meok.ai) — Nutrition tracking, meal logging, and dietary analysis

## Installation

```bash
pip install nutrition-tracker-ai-mcp
```

## Usage

```bash
python server.py
```

## Tools

### `log_meal`
Log a meal with foods and serving sizes. Foods are matched against a built-in nutrition database.

**Parameters:**
- `user_id` (str): User identifier
- `foods` (list): List of food names
- `servings_grams` (list): Serving sizes in grams per food (default: 100g each)
- `meal_type` (str): Meal type: breakfast, lunch, dinner, snack (default: "snack")

### `get_daily_summary`
Get a summary of all meals logged today including macro percentages and calorie breakdown.

**Parameters:**
- `user_id` (str): User identifier

### `check_nutrient_balance`
Check if today's nutrition is balanced against recommended targets based on weight and goal.

**Parameters:**
- `user_id` (str): User identifier
- `weight_kg` (float): Body weight in kg (default: 70)
- `goal` (str): Goal: maintain, loss/cut, gain/bulk/muscle (default: "maintain")

### `suggest_foods`
Suggest foods high in a specific nutrient, optionally filtered by category.

**Parameters:**
- `nutrient` (str): Nutrient: calories, protein, carbs, fat, fiber (default: "protein")
- `category` (str): Category filter: protein, grain, fruit, vegetable, fat, dairy, legume
- `limit` (int): Max results (default: 10)

### `get_calorie_estimate`
Estimate calories for a food item. Matches against database or estimates from description.

**Parameters:**
- `food_description` (str): Food name or description
- `grams` (float): Serving size in grams (default: 100)

## Authentication

Free tier: 15 calls/day. Upgrade at [meok.ai/pricing](https://meok.ai/pricing) for unlimited access.

## License

MIT — MEOK AI Labs

<div align="center">

# Nutrition Tracker Ai MCP

**MCP server for nutrition tracker ai mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-nutrition-tracker-ai-mcp)](https://pypi.org/project/meok-nutrition-tracker-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Nutrition Tracker Ai MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `log_meal` | Log a meal with foods and serving sizes. Foods are matched against built-in data |
| `get_daily_summary` | Get a summary of all meals logged today for a user. |
| `check_nutrient_balance` | Check if today's nutrition is balanced against recommended targets. |
| `suggest_foods` | Suggest foods high in a specific nutrient, optionally filtered by category. |
| `get_calorie_estimate` | Estimate calories for a food item. Matches against database or estimates from de |

## Installation

```bash
pip install meok-nutrition-tracker-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "nutrition-tracker-ai": {
      "command": "python",
      "args": ["-m", "meok_nutrition_tracker_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 5 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)

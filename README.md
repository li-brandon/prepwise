# PrepWise

A meal prep assistant MCP server for Claude Code. Provides tools for recipe parsing, preference learning, grocery list management, and HEB cart automation.

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Claude Code CLI

### Setup

```bash
# Clone and install dependencies
cd /Users/brandonli/dev/personal/prepwise
uv sync

# Install Playwright browsers (for HEB cart automation)
uv run playwright install chromium

# Verify installation
uv run python -c "from prepwise.server import mcp; print('OK')"
```

### Register with Claude Code

The server is already registered. To re-register or register on a new machine:

```bash
claude mcp add --transport stdio --scope user prepwise -- \
  uv --directory /Users/brandonli/dev/personal/prepwise run prepwise
```

## Usage

### Quick Start Commands

Use these slash commands in Claude Code:

| Command | Description |
|---------|-------------|
| `/suggest-recipe dinner` | Get AI-powered recipe suggestions |
| `/add-recipe <url>` | Add a recipe from any URL to Notion |
| `/tiktok-recipe <url>` | Extract recipe from TikTok video |
| `/meal-plan` | Generate a weekly meal plan with macros |
| `/heb-cart` | Fill HEB cart with groceries |

### Example Workflows

**Add a new recipe:**
```
/add-recipe https://www.budgetbytes.com/honey-garlic-chicken/
```

**Get recipe suggestions based on preferences:**
```
/suggest-recipe quick weeknight dinner
```

**Plan meals for the week:**
```
/meal-plan
```

**Learn preferences from your cooking history:**
```
Analyze my meal history from Notion and suggest preference updates
```

## Tools Reference

### Recipe Management

| Tool | Purpose |
|------|---------|
| `prepwise_parse_recipe_url` | Extract recipe from any URL (100+ sites supported) |

### Preference Management

| Tool | Purpose |
|------|---------|
| `prepwise_get_preferences` | Get complete preference profile |
| `prepwise_update_preference` | Update a preference (-2 to +2 rating) |
| `prepwise_update_macro_targets` | Set daily calorie/protein/carb/fat targets |
| `prepwise_update_dietary_restrictions` | Add/remove dietary restrictions |
| `prepwise_get_setup_questions` | Get setup wizard questions |
| `prepwise_complete_setup` | Mark initial setup as complete |
| `prepwise_analyze_meal_history` | Learn preferences from past recipes |

### Favorite Sites

| Tool | Purpose |
|------|---------|
| `prepwise_get_favorite_sites` | List favorite recipe websites |
| `prepwise_add_favorite_site` | Add a site to favorites |
| `prepwise_remove_favorite_site` | Remove a site from favorites |
| `prepwise_get_site_search_queries` | Generate site-specific search queries |

### HEB Cart Automation

| Tool | Purpose |
|------|---------|
| `prepwise_get_heb_session_status` | Check if logged in to HEB |
| `prepwise_heb_login` | Open browser for interactive HEB login |
| `prepwise_add_to_heb_cart` | Add ingredients to HEB cart |

## Preference System

### Rating Scale

| Rating | Meaning |
|--------|---------|
| `-2` | Strongly dislike / hate |
| `-1` | Dislike |
| `0` | Neutral (removes preference) |
| `+1` | Like |
| `+2` | Love |

### Categories

- **Ingredients**: Individual food items (cilantro, mushrooms, olives, etc.)
- **Cuisines**: Cooking styles (Mexican, Italian, Thai, etc.)
- **Cooking Methods**: Preparation styles (slow_cooker, air_fryer, one_pot, etc.)

### First-Time Setup

On first use, `/suggest-recipe` will run a preference setup wizard asking about:
- Common polarizing ingredients (cilantro, mushrooms, olives, etc.)
- Cuisine preferences
- Cooking method preferences
- Dietary restrictions
- Macro targets

## Data Storage

All data is stored locally in `~/.prepwise/`:

| File | Contents |
|------|----------|
| `preferences.json` | User preference profile |
| `favorite_sites.json` | Favorite recipe websites |
| `setup_complete` | Flag indicating setup is done |
| `heb_session/` | Playwright browser session for HEB |

## Notion Integration

PrepWise integrates with two Notion databases:

### My Recipes Database
Stores saved recipes with properties:
- Name, Type, Cuisine, Difficulty, Rating
- Source URL, Prep Time, Cook Time, Servings

### My Weekly Meals
Calendar view for meal planning with:
- Name, Date, Meal Description, Tags

## Development

### Project Structure

```
prepwise/
├── src/prepwise/
│   ├── server.py           # FastMCP server (15 tools)
│   ├── tools/
│   │   ├── preferences.py  # Preference management
│   │   ├── favorite_sites.py
│   │   ├── recipe_parser.py
│   │   ├── heb_cart.py
│   │   └── meal_history.py # Preference learning
│   ├── models/             # Pydantic data models
│   └── storage/            # JSON file storage
├── pyproject.toml
├── CLAUDE.md               # Claude Code instructions
└── README.md
```

### Running Tests

```bash
# Test server imports
uv run python -c "from prepwise.server import mcp; print('OK')"

# List registered tools
uv run python -c "
from prepwise.server import mcp
for t in sorted(mcp._tool_manager._tools.keys()):
    print(f'  {t}')
"

# Test meal history analysis
uv run python -c "
from prepwise.tools.meal_history import analyze_recipes, format_analysis_summary

recipes = [
    {'Name': 'Tacos', 'Cuisine': ['Mexican'], 'Difficulty': 'Easy', 'Rating': '5'},
    {'Name': 'Pasta', 'Cuisine': ['Italian'], 'Difficulty': 'Easy', 'Rating': '4'},
]
print(format_analysis_summary(analyze_recipes(recipes)))
"
```

### Running the Server Directly

```bash
# Start the MCP server (stdio transport)
uv run prepwise
```

## Troubleshooting

### "Import could not be resolved" errors

These are LSP errors from missing the virtual environment. The code runs fine:
```bash
uv run python -c "from prepwise.server import mcp; print('OK')"
```

### HEB login issues

The first time you use `/heb-cart`, you'll need to log in manually:
1. A browser window will open
2. Log in to your HEB account
3. The session is saved for future use

### Recipe parsing fails

Not all sites are supported. The `recipe-scrapers` library supports 100+ sites including:
- AllRecipes, Food Network, Serious Eats, Budget Bytes
- NYT Cooking, Bon Appetit, Epicurious
- And many more

For unsupported sites (like TikTok), use `/tiktok-recipe` which uses AI extraction.

## License

Private project - not for distribution.

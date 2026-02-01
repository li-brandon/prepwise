# PrepWise - Meal Prep Assistant

An MCP server that provides tools for meal prep automation, including recipe parsing, preference learning, grocery list management, and HEB cart automation.

## Quick Start

```bash
# Suggest a recipe based on preferences
/suggest-recipe dinner

# Add a recipe from a URL
/add-recipe https://www.budgetbytes.com/honey-garlic-chicken/

# Add a TikTok recipe
/tiktok-recipe https://www.tiktok.com/@username/video/123

# Plan meals for the week
/meal-plan

# Add groceries to HEB cart
/heb-cart
```

## MCP Server

- **Name:** prepwise
- **Transport:** stdio
- **Command:** `uv --directory /Users/brandonli/dev/personal/prepwise run prepwise`
- **Registered:** User-scoped (available in all projects)

## Tools Available

### Recipe Management
| Tool | Purpose |
|------|---------|
| `prepwise_parse_recipe_url` | Extract recipe from any supported URL (100+ sites) |

### Preference Management
| Tool | Purpose |
|------|---------|
| `prepwise_get_preferences` | Get complete preference profile |
| `prepwise_update_preference` | Update a single preference (-2 to +2 rating) |
| `prepwise_update_macro_targets` | Update daily calorie/protein/carb/fat targets |
| `prepwise_update_dietary_restrictions` | Add/remove dietary restrictions |
| `prepwise_get_setup_questions` | Get pre-populated setup wizard questions |
| `prepwise_complete_setup` | Mark initial setup as complete |
| `prepwise_analyze_meal_history` | Learn preferences from past recipes in Notion |

### Favorite Sites
| Tool | Purpose |
|------|---------|
| `prepwise_get_favorite_sites` | List favorite recipe websites |
| `prepwise_add_favorite_site` | Add a site to favorites |
| `prepwise_remove_favorite_site` | Remove a site from favorites |
| `prepwise_get_site_search_queries` | Generate site-specific search queries |

### HEB Cart
| Tool | Purpose |
|------|---------|
| `prepwise_get_heb_session_status` | Check if logged in to HEB |
| `prepwise_heb_login` | Open browser for interactive HEB login |
| `prepwise_add_to_heb_cart` | Add ingredients to HEB cart |

## Data Locations

- **Preferences:** `~/.prepwise/preferences.json`
- **Favorite Sites:** `~/.prepwise/favorite_sites.json`
- **Setup Flag:** `~/.prepwise/setup_complete`
- **HEB Session:** `~/.prepwise/heb_session/`

## Notion Integration

### My Recipes Database
- **Database ID:** `2f4a986a-8649-8153-aa77-daab8824141a`
- **Data Source ID:** `2f4a986a-8649-81f8-96b2-000b80ef687f`
- **Properties:**
  - `Name` (title): Recipe name
  - `Type` (multi_select): Breakfast, Lunch, Dinner, Dessert, Teatime Foods, Meal Prep Snacks, Event Food, Other, My Recipes
  - `Cuisine` (multi_select): Mexican, Italian, Chinese, Japanese, Indian, Thai, Mediterranean, American, Korean, Vietnamese, Middle Eastern, Greek, French
  - `Source URL` (url): Original recipe link
  - `Prep Time` (number): Minutes
  - `Cook Time` (number): Minutes
  - `Servings` (number): Portion count
  - `Difficulty` (select): Easy, Medium, Hard
  - `Rating` (select): 1-5 stars
  - `Text` (rich_text): Additional notes

### My Weekly Meals
- **Database ID:** `2f4a986a-8649-8170-85ad-d15bea425c10`
- **Data Source ID:** `2f4a986a-8649-8149-940e-000be6c5b130`
- **Properties:**
  - `Name` (title): Meal name
  - `Date` (date): Meal date
  - `Meal Description` (rich_text): Description
  - `Tags` (multi_select): Custom tags
- **Calendar view for meal planning**

### Recipe Book Page
- **Page ID:** `2f4a986a-8649-804b-92c7-d196ee8d8299`

## Related Global Commands

| Command | Location | Description |
|---------|----------|-------------|
| `/tiktok-recipe` | `~/dev/personal/.claude/commands/` | Extract recipe from TikTok video |
| `/add-recipe` | `~/.claude/commands/` | Add recipe from any URL |
| `/meal-plan` | `~/.claude/commands/` | Generate weekly meal plan with macros |
| `/suggest-recipe` | `~/.claude/commands/` | Get AI-powered recipe suggestions |
| `/heb-cart` | `~/.claude/commands/` | Fill HEB cart with groceries |

## Preference System

### Rating Scale
- `-2` = Strongly dislike / hate
- `-1` = Dislike
- `0` = Neutral (removes preference)
- `+1` = Like
- `+2` = Love

### Categories
- **Ingredients:** Individual food items (cilantro, mushrooms, etc.)
- **Cuisines:** Cooking styles (Mexican, Italian, Thai, etc.)
- **Cooking Methods:** Preparation styles (slow_cooker, air_fryer, one_pot, etc.)

### Default Favorite Sites
Pre-populated with:
- Budget Bytes (budgetbytes.com)
- AllRecipes (allrecipes.com)
- Serious Eats (seriouseats.com)

## Development

```bash
# Install dependencies
cd /Users/brandonli/dev/personal/prepwise
uv sync

# Install Playwright browsers
uv run playwright install chromium

# Run server directly (for testing)
uv run prepwise

# Test imports
uv run python -c "from prepwise.server import mcp; print('OK')"
```

## Architecture

```
prepwise/
├── src/prepwise/
│   ├── server.py           # FastMCP server entry point
│   ├── tools/
│   │   ├── preferences.py  # Preference management
│   │   ├── favorite_sites.py # Favorite websites
│   │   ├── recipe_parser.py  # URL parsing with recipe-scrapers
│   │   ├── heb_cart.py     # HEB Playwright automation
│   │   └── meal_history.py # Learn preferences from past meals
│   ├── models/
│   │   ├── preferences.py  # Preference data models
│   │   ├── recipe.py       # Recipe data models
│   │   └── heb.py          # HEB cart models
│   └── storage/
│       ├── paths.py        # Data directory paths
│       └── json_store.py   # JSON file storage
├── pyproject.toml
└── CLAUDE.md
```

## Notes

- HEB automation uses Playwright with a persistent browser context
- User must log in to HEB manually the first time (session is then saved)
- Recipe parser supports 100+ sites via the recipe-scrapers library
- Preference setup wizard asks about common polarizing ingredients

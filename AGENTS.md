# AGENTS.md - Coding Agent Instructions for PrepWise

This file contains instructions for AI coding agents working on this repository.

## Project Overview

PrepWise is an MCP (Model Context Protocol) server for meal prep assistance. It provides tools for recipe parsing, preference learning, grocery list management, and HEB cart automation. The server is built with Python 3.11+ using FastMCP and Pydantic.

## Build, Lint, and Test Commands

### Package Management (uv)

```bash
# Install all dependencies
uv sync

# Add a new dependency
uv add <package>

# Add a dev dependency
uv add --dev <package>
```

### Running the Server

```bash
# Run the MCP server (stdio transport)
uv run prepwise

# Test that imports work
uv run python -c "from prepwise.server import mcp; print('OK')"

# List all registered tools
uv run python -c "from prepwise.server import mcp; print([t for t in mcp._tool_manager._tools.keys()])"
```

### Linting

```bash
# Run ruff linter
uv run ruff check src/

# Run ruff with auto-fix
uv run ruff check --fix src/

# Format code
uv run ruff format src/
```

### Testing

```bash
# No formal test suite yet - use manual testing
# Test a specific module:
uv run python -c "from prepwise.tools.meal_history import analyze_recipes; print('OK')"

# Test with sample data:
uv run python -c "
from prepwise.tools.meal_history import analyze_recipes, format_analysis_summary
recipes = [{'Name': 'Tacos', 'Cuisine': ['Mexican'], 'Difficulty': 'Easy'}]
print(format_analysis_summary(analyze_recipes(recipes)))
"
```

### Playwright Setup (for HEB cart automation)

```bash
uv run playwright install chromium
```

## Code Style Guidelines

### Formatting

- **Line length:** 100 characters max (configured in pyproject.toml)
- **Indentation:** 4 spaces
- **Quotes:** Double quotes for strings
- **Trailing commas:** Use in multi-line structures

### Imports

Order imports as follows (enforced by ruff):

```python
# 1. Standard library
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, TypeVar, Generic

# 2. Third-party packages
import httpx
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright

# 3. Local imports
from prepwise.models.recipe import Recipe
from prepwise.storage.paths import PREPWISE_DIR
```

### Type Annotations

- **Always use type hints** for function parameters and return types
- Use `Optional[T]` or `T | None` for nullable types (Python 3.11+)
- Use `list[T]` and `dict[K, V]` (lowercase) not `List` and `Dict`
- Use `TypeVar` for generic classes

```python
def update_preference(category: str, item: str, rating: int) -> PreferenceProfile:
    ...

async def parse_recipe_url(url: str) -> Recipe:
    ...

def load(self) -> T:  # Generic type from TypeVar
    ...
```

### Naming Conventions

- **Files:** `snake_case.py`
- **Classes:** `PascalCase`
- **Functions/methods:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private functions:** `_leading_underscore`
- **MCP tools:** `prepwise_<action>` (e.g., `prepwise_get_preferences`)

### Docstrings

Use Google-style docstrings:

```python
def parse_recipe_url(url: str) -> Recipe:
    """
    Parse a recipe from a URL using recipe-scrapers.

    Args:
        url: URL to a recipe page

    Returns:
        Parsed Recipe object

    Raises:
        ValueError: If the URL cannot be parsed or website is not supported
    """
```

### Pydantic Models

- Use `Field()` for descriptions and defaults
- Implement helper methods on models when useful
- Group related fields with comments

```python
class Recipe(BaseModel):
    """A complete recipe with all metadata."""

    name: str = Field(description="Recipe name/title")
    description: Optional[str] = Field(default=None, description="Brief description")

    # Timing
    prep_time_minutes: Optional[int] = Field(default=None, description="Prep time in minutes")
    cook_time_minutes: Optional[int] = Field(default=None, description="Cook time in minutes")

    def get_ingredient_names(self) -> list[str]:
        """Get list of ingredient names for preference matching."""
        return [ing.name.lower() for ing in self.ingredients]
```

### Error Handling

- Use specific exceptions where possible
- Log errors with context before re-raising
- Return error dicts from MCP tools instead of raising

```python
# In MCP tool functions - return errors as dicts
@mcp.tool()
async def prepwise_parse_recipe_url(url: str) -> dict:
    try:
        recipe = await recipe_parser.parse_recipe_url(url)
        return recipe.model_dump()
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.exception(f"Error parsing recipe: {e}")
        return {"error": f"Failed to parse recipe: {e}"}

# In internal functions - raise exceptions
async def parse_recipe_url(url: str) -> Recipe:
    try:
        response = await client.get(url)
        response.raise_for_status()
    except httpx.HTTPError as e:
        raise ValueError(f"Failed to fetch URL: {e}")
```

### Logging

- Use module-level loggers
- Log to stderr (important for MCP stdio servers)
- Use appropriate log levels

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing recipe")
logger.warning(f"Could not get cart total: {e}")
logger.exception(f"Error during cart operations: {e}")  # Includes traceback
```

### Async Functions

- Use `async/await` for I/O operations
- Use `httpx.AsyncClient` for HTTP requests
- Use `playwright.async_api` for browser automation

## Project Structure

```
prepwise/
├── src/prepwise/
│   ├── __init__.py
│   ├── server.py           # FastMCP server with tool definitions
│   ├── tools/              # Tool implementations
│   │   ├── preferences.py
│   │   ├── favorite_sites.py
│   │   ├── recipe_parser.py
│   │   ├── heb_cart.py
│   │   └── meal_history.py
│   ├── models/             # Pydantic data models
│   │   ├── preferences.py
│   │   ├── recipe.py
│   │   └── heb.py
│   └── storage/            # File storage utilities
│       ├── paths.py
│       └── json_store.py
├── pyproject.toml          # Project config and dependencies
├── CLAUDE.md               # Claude Code instructions
├── AGENTS.md               # This file
└── README.md               # User documentation
```

## Adding New Tools

1. Create or update a module in `src/prepwise/tools/`
2. Import in `server.py`
3. Add tool function with `@mcp.tool()` decorator
4. Update `CLAUDE.md` tools table
5. Test with `uv run python -c "from prepwise.server import mcp; ..."`

## Key Dependencies

- `mcp[cli]>=1.2.0` - Model Context Protocol server framework
- `pydantic>=2.5.0` - Data validation and models
- `httpx>=0.27.0` - Async HTTP client
- `playwright>=1.40.0` - Browser automation for HEB
- `recipe-scrapers>=15.0.0` - Recipe extraction from URLs
- `beautifulsoup4>=4.12.0` - HTML parsing

## Data Storage

All user data is stored in `~/.prepwise/`:
- `preferences.json` - User preferences (Pydantic model)
- `favorite_sites.json` - Favorite recipe websites
- `setup_complete` - Flag file indicating setup is done
- `heb_session/` - Playwright persistent browser context

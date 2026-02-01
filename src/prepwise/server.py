"""PrepWise MCP Server - Meal prep assistance tools."""

import logging
from typing import Literal

from mcp.server.fastmcp import FastMCP

from prepwise.models.preferences import (
    COMMON_INGREDIENT_QUESTIONS,
    COMMON_CUISINES,
    COMMON_COOKING_METHODS,
    DIETARY_OPTIONS,
)
from prepwise.tools import preferences as pref_tools
from prepwise.tools import favorite_sites as sites_tools
from prepwise.tools import recipe_parser
from prepwise.tools import heb_cart
from prepwise.tools import meal_history

# Configure logging to stderr (important for MCP stdio servers)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("prepwise")


# ============================================================================
# Recipe Parsing Tools
# ============================================================================


@mcp.tool()
async def prepwise_parse_recipe_url(url: str) -> dict:
    """
    Parse a recipe from a URL and extract structured data.

    Supports 100+ recipe websites including AllRecipes, Food Network,
    Serious Eats, Budget Bytes, NYT Cooking, and many more.

    Args:
        url: URL to a recipe page

    Returns:
        Structured recipe with name, ingredients, instructions,
        timing, servings, cuisine, and estimated nutrition
    """
    try:
        recipe = await recipe_parser.parse_recipe_url(url)
        return recipe.model_dump()
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        logger.exception(f"Error parsing recipe: {e}")
        return {"error": f"Failed to parse recipe: {e}"}


# ============================================================================
# Preference Management Tools
# ============================================================================


@mcp.tool()
def prepwise_get_preferences() -> dict:
    """
    Get the user's complete food preference profile.

    Returns:
        Preference profile including:
        - ingredients: dict of ingredient -> rating (-2 to +2)
        - cuisines: dict of cuisine -> rating (-2 to +2)
        - cooking_methods: dict of method -> rating (-2 to +2)
        - macro_targets: daily calorie/protein/carb/fat targets
        - dietary_restrictions: list of restrictions
        - setup_completed: whether initial setup is done
    """
    prefs = pref_tools.load_preferences()
    return prefs.model_dump()


@mcp.tool()
def prepwise_update_preference(
    category: Literal["ingredient", "cuisine", "cooking_method"],
    item: str,
    rating: int,
) -> dict:
    """
    Update a single food preference.

    Args:
        category: Type of preference - "ingredient", "cuisine", or "cooking_method"
        item: The item name (e.g., "cilantro", "Mexican", "slow_cooker")
        rating: Rating from -2 to +2
            -2 = strongly dislike/hate
            -1 = dislike
             0 = neutral (removes the preference)
            +1 = like
            +2 = love

    Returns:
        Updated preference profile
    """
    try:
        prefs = pref_tools.update_preference(category, item, rating)
        return {"success": True, "preferences": prefs.model_dump()}
    except ValueError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def prepwise_update_macro_targets(
    daily_calories: int | None = None,
    daily_protein_g: int | None = None,
    daily_carbs_g: int | None = None,
    daily_fat_g: int | None = None,
) -> dict:
    """
    Update daily macronutrient targets.

    Args:
        daily_calories: Daily calorie target (optional)
        daily_protein_g: Daily protein target in grams (optional)
        daily_carbs_g: Daily carbohydrate target in grams (optional)
        daily_fat_g: Daily fat target in grams (optional)

    Returns:
        Updated preference profile
    """
    prefs = pref_tools.update_macro_targets(
        daily_calories=daily_calories,
        daily_protein_g=daily_protein_g,
        daily_carbs_g=daily_carbs_g,
        daily_fat_g=daily_fat_g,
    )
    return {"success": True, "preferences": prefs.model_dump()}


@mcp.tool()
def prepwise_update_dietary_restrictions(
    add: list[str] | None = None,
    remove: list[str] | None = None,
) -> dict:
    """
    Update dietary restrictions.

    Args:
        add: List of restrictions to add (e.g., ["dairy-free", "gluten-free"])
        remove: List of restrictions to remove

    Returns:
        Updated preference profile
    """
    prefs = pref_tools.load_preferences()

    if add:
        for restriction in add:
            pref_tools.add_dietary_restriction(restriction)

    if remove:
        for restriction in remove:
            pref_tools.remove_dietary_restriction(restriction)

    prefs = pref_tools.load_preferences()
    return {"success": True, "preferences": prefs.model_dump()}


@mcp.tool()
def prepwise_get_setup_questions() -> dict:
    """
    Get the pre-populated questions for initial preference setup.

    This returns the common ingredients, cuisines, cooking methods,
    and dietary options that should be asked during the setup wizard.

    Returns:
        Dictionary with:
        - ingredients: list of (key, display_name) for ingredient questions
        - cuisines: list of cuisine names
        - cooking_methods: list of (key, display_name) for method questions
        - dietary_options: list of dietary restriction options
        - needs_setup: whether user still needs to complete setup
    """
    return {
        "ingredients": COMMON_INGREDIENT_QUESTIONS,
        "cuisines": COMMON_CUISINES,
        "cooking_methods": COMMON_COOKING_METHODS,
        "dietary_options": DIETARY_OPTIONS,
        "needs_setup": pref_tools.needs_setup(),
    }


@mcp.tool()
def prepwise_complete_setup() -> dict:
    """
    Mark the initial preference setup as complete.

    Call this after the user has answered the setup questions.

    Returns:
        Updated preference profile
    """
    prefs = pref_tools.complete_setup()
    return {"success": True, "preferences": prefs.model_dump()}


# ============================================================================
# Favorite Sites Tools
# ============================================================================


@mcp.tool()
def prepwise_get_favorite_sites() -> dict:
    """
    Get the list of favorite recipe websites.

    These sites are prioritized when searching for new recipes.

    Returns:
        Dictionary with:
        - sites: list of {url, name, added_at}
        - domains: list of domains for site: search queries
    """
    sites = sites_tools.load_favorite_sites()
    return {
        "sites": [s.model_dump() for s in sites.sites],
        "domains": sites.get_site_domains(),
    }


@mcp.tool()
def prepwise_add_favorite_site(url: str, name: str) -> dict:
    """
    Add a recipe website to favorites.

    Args:
        url: Base URL of the site (e.g., "https://www.bonappetit.com")
        name: Display name for the site (e.g., "Bon Appetit")

    Returns:
        Updated list of favorite sites
    """
    sites = sites_tools.add_favorite_site(url, name)
    return {
        "success": True,
        "sites": [s.model_dump() for s in sites.sites],
    }


@mcp.tool()
def prepwise_remove_favorite_site(url: str) -> dict:
    """
    Remove a recipe website from favorites.

    Args:
        url: URL of the site to remove

    Returns:
        Updated list of favorite sites
    """
    sites = sites_tools.remove_favorite_site(url)
    return {
        "success": True,
        "sites": [s.model_dump() for s in sites.sites],
    }


@mcp.tool()
def prepwise_get_site_search_queries(query: str) -> dict:
    """
    Generate site-specific search queries for favorite sites.

    Use these queries with a web search tool to prioritize
    results from the user's favorite recipe sites.

    Args:
        query: Base search query (e.g., "quick chicken dinner")

    Returns:
        Dictionary with:
        - queries: list of "site:domain query" strings
        - general_query: the original query for fallback search
    """
    site_queries = sites_tools.get_search_site_queries(query)
    return {
        "queries": site_queries,
        "general_query": query,
    }


# ============================================================================
# HEB Cart Tools
# ============================================================================


@mcp.tool()
async def prepwise_get_heb_session_status() -> dict:
    """
    Check if there's an active HEB session.

    Returns:
        Dictionary with:
        - logged_in: whether user is logged in
        - session_exists: whether a session directory exists
        - message: human-readable status message
    """
    status = await heb_cart.check_session_status()
    return status.model_dump()


@mcp.tool()
async def prepwise_heb_login() -> dict:
    """
    Open HEB login page in a browser for interactive login.

    This opens a visible browser window where the user can log in.
    The session will be saved for future use.

    Returns:
        Dictionary with:
        - success: whether browser was opened successfully
        - message: instructions for the user
    """
    try:
        message = await heb_cart.open_heb_login()
        return {"success": True, "message": message}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
async def prepwise_add_to_heb_cart(ingredients: list[str]) -> dict:
    """
    Add ingredients to HEB cart by searching and adding products.

    This opens a visible browser window and adds each ingredient.
    The user can watch the process and the browser stays open
    for review afterward.

    Args:
        ingredients: List of ingredient strings
            Examples: ["2 lbs chicken thighs", "1 large onion", "garlic"]

    Returns:
        Dictionary with:
        - items: list of items processed with success/failure status
        - total_added: count of items successfully added
        - total_not_found: count of items not found
        - total_errors: count of errors
        - cart_total: estimated cart total (if available)
        - cart_url: URL to view cart
        - summary: human-readable summary
    """
    try:
        result = await heb_cart.add_items_to_cart(ingredients)
        return {
            **result.model_dump(),
            "summary": result.summary(),
        }
    except Exception as e:
        logger.exception(f"Error adding to HEB cart: {e}")
        return {"error": str(e)}


# ============================================================================
# Meal History Learning Tools
# ============================================================================


@mcp.tool()
def prepwise_analyze_meal_history(recipes: list[dict]) -> dict:
    """
    Analyze meal history to learn preferences from past meals.

    Pass recipes from your Notion "My Recipes Database" to get insights
    about cuisine preferences, cooking patterns, and suggested preference
    updates based on actual usage.

    Args:
        recipes: List of recipe dicts from Notion with fields:
            - Name: str (recipe name)
            - Cuisine: list[str] (e.g., ["Mexican", "Italian"])
            - Type: list[str] (e.g., ["Dinner", "Lunch"])
            - Difficulty: str ("Easy", "Medium", "Hard")
            - Rating: str ("1" to "5")
            - Prep Time: int (minutes, optional)
            - Cook Time: int (minutes, optional)

    Returns:
        Dictionary with:
        - cuisine_counts: count of recipes by cuisine
        - meal_type_counts: count of recipes by meal type
        - difficulty_counts: count by difficulty level
        - rating_distribution: count of recipes by rating
        - favorite_cuisines: top cuisines by frequency
        - avoided_cuisines: cuisines not used (if enough data)
        - preferred_difficulty: most common difficulty
        - average_prep_time: average prep time in minutes
        - average_cook_time: average cook time in minutes
        - total_recipes: total number of recipes analyzed
        - suggested_updates: list of preference updates to consider
        - summary: human-readable summary markdown

    Example usage:
        1. Fetch recipes from Notion My Recipes Database
        2. Pass them to this tool
        3. Review suggested preference updates
        4. Apply updates with prepwise_update_preference
    """
    try:
        analysis = meal_history.analyze_recipes(recipes)
        summary = meal_history.format_analysis_summary(analysis)

        return {
            "cuisine_counts": analysis.cuisine_counts,
            "meal_type_counts": analysis.meal_type_counts,
            "difficulty_counts": analysis.difficulty_counts,
            "rating_distribution": analysis.rating_distribution,
            "favorite_cuisines": analysis.favorite_cuisines,
            "avoided_cuisines": analysis.avoided_cuisines,
            "preferred_difficulty": analysis.preferred_difficulty,
            "average_prep_time": analysis.average_prep_time,
            "average_cook_time": analysis.average_cook_time,
            "total_recipes": analysis.total_recipes,
            "suggested_updates": analysis.suggested_updates,
            "summary": summary,
        }
    except Exception as e:
        logger.exception(f"Error analyzing meal history: {e}")
        return {"error": str(e)}


# ============================================================================
# Resources
# ============================================================================


@mcp.resource("prepwise://preferences")
def get_preferences_resource() -> str:
    """
    Get the current user preference profile as a resource.

    This provides read-only access to preferences.
    """
    prefs = pref_tools.load_preferences()

    lines = [
        "# PrepWise User Preferences",
        "",
        "## Setup Status",
        f"Completed: {'Yes' if prefs.setup_completed else 'No'}",
        "",
        "## Macro Targets",
        f"- Calories: {prefs.macro_targets.daily_calories}",
        f"- Protein: {prefs.macro_targets.daily_protein_g}g",
        f"- Carbs: {prefs.macro_targets.daily_carbs_g}g",
        f"- Fat: {prefs.macro_targets.daily_fat_g}g",
        "",
    ]

    if prefs.dietary_restrictions:
        lines.append("## Dietary Restrictions")
        for r in prefs.dietary_restrictions:
            lines.append(f"- {r}")
        lines.append("")

    if prefs.ingredients:
        lines.append("## Ingredient Preferences")
        for ing, rating in sorted(prefs.ingredients.items(), key=lambda x: -x[1]):
            emoji = {2: "love", 1: "like", -1: "dislike", -2: "hate"}.get(rating, "neutral")
            lines.append(f"- {ing}: {emoji} ({rating:+d})")
        lines.append("")

    if prefs.cuisines:
        lines.append("## Cuisine Preferences")
        for cuisine, rating in sorted(prefs.cuisines.items(), key=lambda x: -x[1]):
            emoji = {2: "love", 1: "like", -1: "dislike", -2: "hate"}.get(rating, "neutral")
            lines.append(f"- {cuisine}: {emoji} ({rating:+d})")
        lines.append("")

    if prefs.cooking_methods:
        lines.append("## Cooking Method Preferences")
        for method, rating in sorted(prefs.cooking_methods.items(), key=lambda x: -x[1]):
            emoji = {2: "love", 1: "like", -1: "dislike", -2: "hate"}.get(rating, "neutral")
            lines.append(f"- {method}: {emoji} ({rating:+d})")

    return "\n".join(lines)


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Run the PrepWise MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

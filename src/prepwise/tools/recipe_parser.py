"""Recipe URL parsing using recipe-scrapers library."""

import logging
from typing import Optional
from urllib.parse import urlparse

import httpx
from recipe_scrapers import scrape_html
from recipe_scrapers._exceptions import WebsiteNotImplementedError

from prepwise.models.recipe import Recipe, RecipeIngredient, RecipeNutrition

logger = logging.getLogger(__name__)

# User agent for requests
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def extract_domain(url: str) -> str:
    """Extract domain name from URL for source_name."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    # Capitalize nicely
    parts = domain.split(".")
    if len(parts) >= 2:
        return parts[0].title()
    return domain.title()


def parse_ingredient(raw: str) -> RecipeIngredient:
    """
    Parse a raw ingredient string into structured data.

    This is a simple parser - for more complex parsing,
    consider using a dedicated library like ingredient-parser-nlp.
    """
    raw = raw.strip()

    # Simple extraction - just store raw text for now
    # More sophisticated parsing could be added later
    return RecipeIngredient(
        name=raw,
        raw_text=raw,
    )


def estimate_meal_type(recipe_name: str, ingredients: list[str]) -> Optional[str]:
    """Estimate meal type from recipe name and ingredients."""
    name_lower = recipe_name.lower()
    ingredients_text = " ".join(ingredients).lower()

    # Breakfast indicators
    breakfast_keywords = [
        "breakfast",
        "pancake",
        "waffle",
        "oatmeal",
        "egg",
        "bacon",
        "french toast",
        "muffin",
        "smoothie",
        "cereal",
        "granola",
        "omelet",
        "frittata",
        "hash brown",
    ]
    if any(kw in name_lower or kw in ingredients_text[:200] for kw in breakfast_keywords):
        return "Breakfast"

    # Dessert indicators
    dessert_keywords = [
        "cake",
        "cookie",
        "brownie",
        "pie",
        "ice cream",
        "dessert",
        "chocolate",
        "pudding",
        "cheesecake",
        "tart",
        "sweet",
        "candy",
        "frosting",
        "cupcake",
    ]
    if any(kw in name_lower for kw in dessert_keywords):
        return "Dessert"

    # Snack indicators
    snack_keywords = ["snack", "dip", "appetizer", "chip", "popcorn", "bite"]
    if any(kw in name_lower for kw in snack_keywords):
        return "Snack"

    # Default to Dinner for main dishes
    return "Dinner"


def estimate_cuisine(recipe_name: str, ingredients: list[str]) -> Optional[str]:
    """Estimate cuisine type from recipe name and ingredients."""
    name_lower = recipe_name.lower()
    ingredients_text = " ".join(ingredients).lower()
    combined = f"{name_lower} {ingredients_text}"

    cuisine_indicators = {
        "Mexican": [
            "taco",
            "burrito",
            "enchilada",
            "salsa",
            "tortilla",
            "jalapeño",
            "cilantro",
            "cumin",
            "mexican",
        ],
        "Italian": [
            "pasta",
            "pizza",
            "risotto",
            "parmesan",
            "marinara",
            "italian",
            "basil",
            "oregano",
        ],
        "Chinese": ["soy sauce", "wok", "stir fry", "chinese", "ginger", "sesame", "bok choy"],
        "Japanese": ["sushi", "ramen", "miso", "japanese", "teriyaki", "wasabi", "nori"],
        "Indian": ["curry", "masala", "tikka", "indian", "turmeric", "garam", "naan", "paneer"],
        "Thai": ["thai", "coconut milk", "fish sauce", "lemongrass", "pad thai", "basil"],
        "Mediterranean": ["mediterranean", "hummus", "falafel", "tahini", "olive", "feta"],
        "Korean": ["korean", "kimchi", "gochujang", "bulgogi", "bibimbap"],
        "American": ["burger", "bbq", "mac and cheese", "american", "hot dog"],
        "Greek": ["greek", "tzatziki", "gyro", "feta", "yogurt"],
        "French": ["french", "croissant", "baguette", "brie", "coq au vin"],
    }

    for cuisine, keywords in cuisine_indicators.items():
        if any(kw in combined for kw in keywords):
            return cuisine

    return None


def estimate_difficulty(prep_time: Optional[int], cook_time: Optional[int], num_steps: int) -> str:
    """Estimate recipe difficulty."""
    total_time = (prep_time or 0) + (cook_time or 0)

    if total_time <= 30 and num_steps <= 6:
        return "Easy"
    elif total_time <= 60 and num_steps <= 12:
        return "Medium"
    else:
        return "Hard"


async def parse_recipe_url(url: str) -> Recipe:
    """
    Parse a recipe from a URL using recipe-scrapers.

    Args:
        url: URL to a recipe page

    Returns:
        Parsed Recipe object

    Raises:
        ValueError: If the URL cannot be parsed or website is not supported
    """
    # Fetch the HTML
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url,
                headers={"User-Agent": USER_AGENT},
                follow_redirects=True,
                timeout=30.0,
            )
            response.raise_for_status()
            html = response.text
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to fetch URL: {e}")

    # Parse with recipe-scrapers
    try:
        scraper = scrape_html(html, org_url=url)
    except WebsiteNotImplementedError:
        raise ValueError(
            f"Website not supported by recipe-scrapers. "
            f"Supported sites: https://github.com/hhursev/recipe-scrapers#scrapers-available-for"
        )
    except Exception as e:
        raise ValueError(f"Failed to parse recipe: {e}")

    # Extract data with fallbacks
    def safe_get(method, default=None):
        try:
            result = method()
            return result if result else default
        except Exception:
            return default

    name = safe_get(scraper.title, "Unknown Recipe")
    ingredients_raw = safe_get(scraper.ingredients, [])
    instructions_raw = safe_get(scraper.instructions, "")

    # Parse instructions into steps
    if isinstance(instructions_raw, str):
        # Split by newlines or numbered steps
        instructions = [
            step.strip()
            for step in instructions_raw.replace("\n\n", "\n").split("\n")
            if step.strip()
        ]
    else:
        instructions = instructions_raw or []

    # Parse ingredients
    ingredients = [parse_ingredient(ing) for ing in ingredients_raw]

    # Get timing
    prep_time = safe_get(scraper.prep_time)
    cook_time = safe_get(scraper.cook_time)
    total_time = safe_get(scraper.total_time)

    # Convert timing to minutes if needed
    def to_minutes(val) -> Optional[int]:
        if val is None:
            return None
        if isinstance(val, int):
            return val
        # recipe-scrapers usually returns int, but handle string just in case
        try:
            return int(val)
        except (ValueError, TypeError):
            return None

    prep_time_min = to_minutes(prep_time)
    cook_time_min = to_minutes(cook_time)
    total_time_min = to_minutes(total_time)

    # Get servings
    servings = None
    yields = safe_get(scraper.yields)
    if yields:
        # Try to extract number from yields string like "4 servings"
        import re

        match = re.search(r"(\d+)", str(yields))
        if match:
            servings = int(match.group(1))

    # Estimate categorization
    meal_type = estimate_meal_type(name, ingredients_raw)
    cuisine = estimate_cuisine(name, ingredients_raw)
    difficulty = estimate_difficulty(prep_time_min, cook_time_min, len(instructions))

    # Get nutrition if available
    nutrition = None
    nutrients = safe_get(scraper.nutrients)
    if nutrients and isinstance(nutrients, dict):

        def extract_nutrient(key: str) -> Optional[float]:
            val = nutrients.get(key)
            if val is None:
                return None
            # Remove units and convert to float
            import re

            match = re.search(r"([\d.]+)", str(val))
            if match:
                return float(match.group(1))
            return None

        nutrition = RecipeNutrition(
            calories=int(extract_nutrient("calories") or 0) or None,
            protein_g=extract_nutrient("proteinContent"),
            carbs_g=extract_nutrient("carbohydrateContent"),
            fat_g=extract_nutrient("fatContent"),
            fiber_g=extract_nutrient("fiberContent"),
            sodium_mg=extract_nutrient("sodiumContent"),
        )

    # Build recipe object
    return Recipe(
        name=name,
        description=safe_get(scraper.description),
        source_url=url,
        source_name=extract_domain(url),
        author=safe_get(scraper.author),
        ingredients=ingredients,
        ingredients_raw=ingredients_raw,
        instructions=instructions,
        prep_time_minutes=prep_time_min,
        cook_time_minutes=cook_time_min,
        total_time_minutes=total_time_min,
        servings=servings,
        meal_type=meal_type,
        cuisine=cuisine,
        difficulty=difficulty,
        nutrition=nutrition,
        image_url=safe_get(scraper.image),
        tags=[],
        dietary_info=[],
    )

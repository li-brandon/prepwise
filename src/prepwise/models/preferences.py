"""Preference data models for PrepWise."""

from pydantic import BaseModel, Field


class MacroTargets(BaseModel):
    """Daily macronutrient targets."""

    daily_calories: int = Field(default=2000, description="Daily calorie target")
    daily_protein_g: int = Field(default=150, description="Daily protein target in grams")
    daily_carbs_g: int = Field(default=200, description="Daily carbohydrate target in grams")
    daily_fat_g: int = Field(default=70, description="Daily fat target in grams")


class PreferenceProfile(BaseModel):
    """
    User's complete food preference profile.

    Rating scale: -2 (strongly dislike) to +2 (love), 0 = neutral
    """

    # Ingredient preferences: ingredient_name -> rating (-2 to +2)
    ingredients: dict[str, int] = Field(
        default_factory=dict, description="Ingredient preferences: -2 (hate) to +2 (love)"
    )

    # Cuisine preferences: cuisine_name -> rating (-2 to +2)
    cuisines: dict[str, int] = Field(
        default_factory=dict, description="Cuisine preferences: -2 (hate) to +2 (love)"
    )

    # Cooking method preferences: method_name -> rating (-2 to +2)
    cooking_methods: dict[str, int] = Field(
        default_factory=dict, description="Cooking method preferences: -2 (hate) to +2 (love)"
    )

    # Macro targets
    macro_targets: MacroTargets = Field(
        default_factory=MacroTargets, description="Daily macronutrient targets"
    )

    # Dietary restrictions (e.g., "dairy-free", "gluten-free", "vegetarian")
    dietary_restrictions: list[str] = Field(
        default_factory=list, description="Dietary restrictions and allergies"
    )

    # Whether initial setup has been completed
    setup_completed: bool = Field(
        default=False, description="Whether the user has completed initial preference setup"
    )

    def get_liked_ingredients(self) -> list[str]:
        """Get ingredients with positive ratings (+1 or +2)."""
        return [k for k, v in self.ingredients.items() if v > 0]

    def get_disliked_ingredients(self) -> list[str]:
        """Get ingredients with negative ratings (-1 or -2)."""
        return [k for k, v in self.ingredients.items() if v < 0]

    def get_liked_cuisines(self) -> list[str]:
        """Get cuisines with positive ratings (+1 or +2)."""
        return [k for k, v in self.cuisines.items() if v > 0]

    def get_disliked_cuisines(self) -> list[str]:
        """Get cuisines with negative ratings (-1 or -2)."""
        return [k for k, v in self.cuisines.items() if v < 0]

    def get_preferred_methods(self) -> list[str]:
        """Get cooking methods with positive ratings (+1 or +2)."""
        return [k for k, v in self.cooking_methods.items() if v > 0]


# Pre-populated questions for setup wizard
COMMON_INGREDIENT_QUESTIONS = [
    ("cilantro", "cilantro/coriander"),
    ("mushrooms", "mushrooms"),
    ("olives", "olives"),
    ("spicy_food", "spicy food"),
    ("seafood", "seafood"),
    ("tofu", "tofu"),
    ("avocado", "avocado"),
    ("coconut", "coconut"),
    ("blue_cheese", "blue cheese / strong cheeses"),
    ("raw_onion", "raw onions"),
    ("bell_peppers", "bell peppers"),
    ("eggplant", "eggplant"),
    ("beans", "beans/legumes"),
    ("nuts", "nuts"),
]

COMMON_CUISINES = [
    "Mexican",
    "Italian",
    "Chinese",
    "Japanese",
    "Indian",
    "Thai",
    "Mediterranean",
    "American",
    "Korean",
    "Vietnamese",
    "Middle Eastern",
    "Greek",
    "French",
]

COMMON_COOKING_METHODS = [
    ("quick_meals", "Quick meals (under 30 min)"),
    ("slow_cooker", "Slow cooker / crockpot"),
    ("air_fryer", "Air fryer"),
    ("grilling", "Grilling / BBQ"),
    ("meal_prep", "Batch cooking / meal prep"),
    ("one_pot", "One-pot meals"),
    ("sheet_pan", "Sheet pan dinners"),
    ("instant_pot", "Instant Pot / pressure cooker"),
    ("stir_fry", "Stir fry"),
    ("baking", "Baking"),
]

DIETARY_OPTIONS = [
    "dairy-free",
    "gluten-free",
    "vegetarian",
    "vegan",
    "keto",
    "low-carb",
    "nut-free",
    "egg-free",
    "pescatarian",
    "halal",
    "kosher",
]

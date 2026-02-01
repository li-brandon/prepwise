"""Recipe data models for PrepWise."""

from pydantic import BaseModel, Field
from typing import Optional


class RecipeIngredient(BaseModel):
    """A single ingredient in a recipe."""

    name: str = Field(description="Ingredient name")
    quantity: Optional[str] = Field(default=None, description="Quantity (e.g., '2', '1/2')")
    unit: Optional[str] = Field(default=None, description="Unit (e.g., 'cups', 'lbs', 'cloves')")
    notes: Optional[str] = Field(
        default=None, description="Additional notes (e.g., 'diced', 'optional')"
    )
    raw_text: str = Field(description="Original ingredient text as parsed")

    def __str__(self) -> str:
        """Return human-readable ingredient string."""
        parts = []
        if self.quantity:
            parts.append(self.quantity)
        if self.unit:
            parts.append(self.unit)
        parts.append(self.name)
        if self.notes:
            parts.append(f"({self.notes})")
        return " ".join(parts)


class RecipeNutrition(BaseModel):
    """Estimated nutritional information per serving."""

    calories: Optional[int] = Field(default=None, description="Calories per serving")
    protein_g: Optional[float] = Field(default=None, description="Protein in grams")
    carbs_g: Optional[float] = Field(default=None, description="Carbohydrates in grams")
    fat_g: Optional[float] = Field(default=None, description="Fat in grams")
    fiber_g: Optional[float] = Field(default=None, description="Fiber in grams")
    sodium_mg: Optional[float] = Field(default=None, description="Sodium in milligrams")


class Recipe(BaseModel):
    """A complete recipe with all metadata."""

    name: str = Field(description="Recipe name/title")
    description: Optional[str] = Field(default=None, description="Brief description of the dish")

    # Source information
    source_url: Optional[str] = Field(
        default=None, description="Original URL where recipe was found"
    )
    source_name: Optional[str] = Field(
        default=None, description="Name of the source (e.g., 'AllRecipes', 'Budget Bytes')"
    )
    author: Optional[str] = Field(default=None, description="Recipe author if available")

    # Ingredients and instructions
    ingredients: list[RecipeIngredient] = Field(
        default_factory=list, description="List of ingredients"
    )
    ingredients_raw: list[str] = Field(
        default_factory=list, description="Raw ingredient strings as parsed"
    )
    instructions: list[str] = Field(default_factory=list, description="Step-by-step instructions")

    # Time and servings
    prep_time_minutes: Optional[int] = Field(
        default=None, description="Preparation time in minutes"
    )
    cook_time_minutes: Optional[int] = Field(default=None, description="Cooking time in minutes")
    total_time_minutes: Optional[int] = Field(default=None, description="Total time in minutes")
    servings: Optional[int] = Field(default=None, description="Number of servings")

    # Categorization
    meal_type: Optional[str] = Field(
        default=None, description="Meal type: Breakfast, Lunch, Dinner, Dessert, Snack, etc."
    )
    cuisine: Optional[str] = Field(default=None, description="Cuisine type: Mexican, Italian, etc.")
    difficulty: Optional[str] = Field(default=None, description="Difficulty: Easy, Medium, Hard")

    # Nutrition (estimated or from source)
    nutrition: Optional[RecipeNutrition] = Field(
        default=None, description="Nutritional information"
    )

    # Tags and categories
    tags: list[str] = Field(default_factory=list, description="Recipe tags/categories")
    dietary_info: list[str] = Field(
        default_factory=list, description="Dietary labels: dairy-free, vegan, etc."
    )

    # Image
    image_url: Optional[str] = Field(default=None, description="URL to recipe image")

    @property
    def total_time(self) -> Optional[int]:
        """Calculate total time from prep and cook time if not directly available."""
        if self.total_time_minutes:
            return self.total_time_minutes
        if self.prep_time_minutes and self.cook_time_minutes:
            return self.prep_time_minutes + self.cook_time_minutes
        return self.prep_time_minutes or self.cook_time_minutes

    def get_ingredient_names(self) -> list[str]:
        """Get list of ingredient names for preference matching."""
        return [ing.name.lower() for ing in self.ingredients]

    def to_markdown(self) -> str:
        """Convert recipe to markdown format for Notion."""
        lines = []

        if self.description:
            lines.append(self.description)
            lines.append("")

        # Time info
        time_parts = []
        if self.prep_time_minutes:
            time_parts.append(f"Prep: {self.prep_time_minutes} min")
        if self.cook_time_minutes:
            time_parts.append(f"Cook: {self.cook_time_minutes} min")
        if self.servings:
            time_parts.append(f"Servings: {self.servings}")
        if time_parts:
            lines.append(" | ".join(time_parts))
            lines.append("")

        # Ingredients
        lines.append("**Ingredients**")
        for ing in self.ingredients_raw or [str(i) for i in self.ingredients]:
            lines.append(f"- {ing}")
        lines.append("")

        # Instructions
        lines.append("**Instructions**")
        for i, step in enumerate(self.instructions, 1):
            lines.append(f"{i}. {step}")
        lines.append("")

        # Source credit
        if self.source_url:
            source_text = self.source_name or "Source"
            lines.append(f"*Recipe from [{source_text}]({self.source_url})*")

        return "\n".join(lines)

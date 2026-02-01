"""Preference management tools for PrepWise."""

from prepwise.models.preferences import (
    PreferenceProfile,
    MacroTargets,
    COMMON_INGREDIENT_QUESTIONS,
    COMMON_CUISINES,
    COMMON_COOKING_METHODS,
    DIETARY_OPTIONS,
)
from prepwise.storage.json_store import JSONStore
from prepwise.storage.paths import PREFERENCES_FILE, mark_setup_complete, is_setup_complete


def get_preferences_store() -> JSONStore[PreferenceProfile]:
    """Get the preferences JSON store."""
    return JSONStore(PREFERENCES_FILE, PreferenceProfile)


def load_preferences() -> PreferenceProfile:
    """Load user preferences from storage."""
    store = get_preferences_store()
    return store.load()


def save_preferences(prefs: PreferenceProfile) -> None:
    """Save user preferences to storage."""
    store = get_preferences_store()
    store.save(prefs)


def update_preference(category: str, item: str, rating: int) -> PreferenceProfile:
    """
    Update a single preference.

    Args:
        category: One of "ingredient", "cuisine", "cooking_method"
        item: The item name (e.g., "cilantro", "Mexican", "slow_cooker")
        rating: Rating from -2 (hate) to +2 (love), 0 = neutral

    Returns:
        Updated preference profile
    """
    if rating < -2 or rating > 2:
        raise ValueError("Rating must be between -2 and +2")

    prefs = load_preferences()

    # Normalize item name
    item_key = item.lower().strip().replace(" ", "_")

    if category == "ingredient":
        if rating == 0:
            prefs.ingredients.pop(item_key, None)
        else:
            prefs.ingredients[item_key] = rating
    elif category == "cuisine":
        # Keep cuisine names capitalized for display
        item_display = item.strip().title()
        if rating == 0:
            prefs.cuisines.pop(item_display, None)
        else:
            prefs.cuisines[item_display] = rating
    elif category == "cooking_method":
        if rating == 0:
            prefs.cooking_methods.pop(item_key, None)
        else:
            prefs.cooking_methods[item_key] = rating
    else:
        raise ValueError(
            f"Unknown category: {category}. Must be 'ingredient', 'cuisine', or 'cooking_method'"
        )

    save_preferences(prefs)
    return prefs


def update_macro_targets(
    daily_calories: int | None = None,
    daily_protein_g: int | None = None,
    daily_carbs_g: int | None = None,
    daily_fat_g: int | None = None,
) -> PreferenceProfile:
    """Update macro targets."""
    prefs = load_preferences()

    if daily_calories is not None:
        prefs.macro_targets.daily_calories = daily_calories
    if daily_protein_g is not None:
        prefs.macro_targets.daily_protein_g = daily_protein_g
    if daily_carbs_g is not None:
        prefs.macro_targets.daily_carbs_g = daily_carbs_g
    if daily_fat_g is not None:
        prefs.macro_targets.daily_fat_g = daily_fat_g

    save_preferences(prefs)
    return prefs


def add_dietary_restriction(restriction: str) -> PreferenceProfile:
    """Add a dietary restriction."""
    prefs = load_preferences()
    restriction_normalized = restriction.lower().strip()

    if restriction_normalized not in prefs.dietary_restrictions:
        prefs.dietary_restrictions.append(restriction_normalized)
        save_preferences(prefs)

    return prefs


def remove_dietary_restriction(restriction: str) -> PreferenceProfile:
    """Remove a dietary restriction."""
    prefs = load_preferences()
    restriction_normalized = restriction.lower().strip()

    if restriction_normalized in prefs.dietary_restrictions:
        prefs.dietary_restrictions.remove(restriction_normalized)
        save_preferences(prefs)

    return prefs


def complete_setup() -> PreferenceProfile:
    """Mark setup as complete."""
    prefs = load_preferences()
    prefs.setup_completed = True
    save_preferences(prefs)
    mark_setup_complete()
    return prefs


def get_setup_questions() -> dict:
    """
    Get the pre-populated setup questions for the wizard.

    Returns a dict with:
    - ingredients: list of (key, display_name) tuples
    - cuisines: list of cuisine names
    - cooking_methods: list of (key, display_name) tuples
    - dietary_options: list of dietary restriction options
    """
    return {
        "ingredients": COMMON_INGREDIENT_QUESTIONS,
        "cuisines": COMMON_CUISINES,
        "cooking_methods": COMMON_COOKING_METHODS,
        "dietary_options": DIETARY_OPTIONS,
    }


def needs_setup() -> bool:
    """Check if user needs to complete initial setup."""
    prefs = load_preferences()
    return not prefs.setup_completed and not is_setup_complete()

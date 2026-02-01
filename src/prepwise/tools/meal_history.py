"""Meal history analysis tools for learning preferences from past meals."""

from collections import Counter
from dataclasses import dataclass


@dataclass
class MealHistoryAnalysis:
    """Results from analyzing meal history."""

    # Counts by category
    cuisine_counts: dict[str, int]
    meal_type_counts: dict[str, int]
    difficulty_counts: dict[str, int]
    rating_distribution: dict[str, int]

    # Derived insights
    favorite_cuisines: list[str]  # Top cuisines by frequency
    avoided_cuisines: list[str]  # Cuisines with low/no usage
    preferred_difficulty: str | None  # Most common difficulty
    average_prep_time: float | None  # Average prep time in minutes
    average_cook_time: float | None  # Average cook time in minutes
    total_recipes: int

    # Suggested preference updates
    suggested_updates: list[dict]


def analyze_recipes(recipes: list[dict]) -> MealHistoryAnalysis:
    """
    Analyze a list of recipes from the user's recipe database.

    Args:
        recipes: List of recipe dicts with keys:
            - Name: str
            - Cuisine: list[str] or JSON string
            - Type: list[str] or JSON string
            - Difficulty: str
            - Rating: str (1-5)
            - Prep Time: int (minutes)
            - Cook Time: int (minutes)

    Returns:
        MealHistoryAnalysis with counts, insights, and suggested preference updates
    """
    import json

    cuisine_counter: Counter[str] = Counter()
    meal_type_counter: Counter[str] = Counter()
    difficulty_counter: Counter[str] = Counter()
    rating_counter: Counter[str] = Counter()
    prep_times: list[float] = []
    cook_times: list[float] = []

    # All known cuisines for detecting avoided ones
    all_cuisines = {
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
    }

    for recipe in recipes:
        # Parse cuisines (could be list or JSON string)
        cuisines = recipe.get("Cuisine", [])
        if isinstance(cuisines, str):
            try:
                cuisines = json.loads(cuisines)
            except json.JSONDecodeError:
                cuisines = [cuisines] if cuisines else []

        for cuisine in cuisines:
            cuisine_counter[cuisine] += 1

        # Parse meal types
        meal_types = recipe.get("Type", [])
        if isinstance(meal_types, str):
            try:
                meal_types = json.loads(meal_types)
            except json.JSONDecodeError:
                meal_types = [meal_types] if meal_types else []

        for meal_type in meal_types:
            meal_type_counter[meal_type] += 1

        # Difficulty
        difficulty = recipe.get("Difficulty")
        if difficulty:
            difficulty_counter[difficulty] += 1

        # Rating
        rating = recipe.get("Rating")
        if rating:
            rating_counter[str(rating)] += 1

        # Timing
        prep_time = recipe.get("Prep Time")
        if prep_time is not None:
            prep_times.append(float(prep_time))

        cook_time = recipe.get("Cook Time")
        if cook_time is not None:
            cook_times.append(float(cook_time))

    # Derive insights
    total_recipes = len(recipes)

    # Favorite cuisines (top 3 by count, with at least 2 recipes)
    favorite_cuisines = [
        cuisine for cuisine, count in cuisine_counter.most_common(5) if count >= 2
    ][:3]

    # Avoided cuisines (known cuisines with 0 usage when user has 5+ recipes)
    used_cuisines = set(cuisine_counter.keys())
    avoided_cuisines = []
    if total_recipes >= 5:
        avoided_cuisines = list(all_cuisines - used_cuisines)

    # Preferred difficulty
    preferred_difficulty = None
    if difficulty_counter:
        preferred_difficulty = difficulty_counter.most_common(1)[0][0]

    # Average times
    average_prep_time = sum(prep_times) / len(prep_times) if prep_times else None
    average_cook_time = sum(cook_times) / len(cook_times) if cook_times else None

    # Generate suggested preference updates
    suggested_updates = _generate_suggestions(
        cuisine_counter=cuisine_counter,
        rating_counter=rating_counter,
        total_recipes=total_recipes,
        favorite_cuisines=favorite_cuisines,
        avoided_cuisines=avoided_cuisines,
        preferred_difficulty=preferred_difficulty,
        average_prep_time=average_prep_time,
        average_cook_time=average_cook_time,
    )

    return MealHistoryAnalysis(
        cuisine_counts=dict(cuisine_counter),
        meal_type_counts=dict(meal_type_counter),
        difficulty_counts=dict(difficulty_counter),
        rating_distribution=dict(rating_counter),
        favorite_cuisines=favorite_cuisines,
        avoided_cuisines=avoided_cuisines,
        preferred_difficulty=preferred_difficulty,
        average_prep_time=round(average_prep_time, 1) if average_prep_time else None,
        average_cook_time=round(average_cook_time, 1) if average_cook_time else None,
        total_recipes=total_recipes,
        suggested_updates=suggested_updates,
    )


def _generate_suggestions(
    cuisine_counter: Counter[str],
    rating_counter: Counter[str],
    total_recipes: int,
    favorite_cuisines: list[str],
    avoided_cuisines: list[str],
    preferred_difficulty: str | None,
    average_prep_time: float | None,
    average_cook_time: float | None,
) -> list[dict]:
    """Generate preference update suggestions based on analysis."""
    suggestions: list[dict] = []

    # Skip suggestions if not enough data
    if total_recipes < 3:
        return suggestions

    # Suggest liking frequently used cuisines
    for cuisine in favorite_cuisines:
        count = cuisine_counter.get(cuisine, 0)
        # Strong preference if used in >30% of recipes
        if count / total_recipes > 0.3:
            suggestions.append(
                {
                    "category": "cuisine",
                    "item": cuisine,
                    "suggested_rating": 2,
                    "reason": f"You've made {count} {cuisine} recipes ({count * 100 // total_recipes}% of your collection)",
                    "confidence": "high",
                }
            )
        elif count / total_recipes > 0.15:
            suggestions.append(
                {
                    "category": "cuisine",
                    "item": cuisine,
                    "suggested_rating": 1,
                    "reason": f"You've made {count} {cuisine} recipes",
                    "confidence": "medium",
                }
            )

    # Suggest cooking method preferences based on difficulty
    if preferred_difficulty:
        method_map = {
            "Easy": [("one_pot", 1), ("sheet_pan", 1), ("slow_cooker", 1)],
            "Medium": [("air_fryer", 1), ("instant_pot", 1)],
            "Hard": [("sous_vide", 1), ("smoking", 1)],
        }
        for method, rating in method_map.get(preferred_difficulty, []):
            suggestions.append(
                {
                    "category": "cooking_method",
                    "item": method,
                    "suggested_rating": rating,
                    "reason": f"You tend to prefer {preferred_difficulty.lower()} recipes",
                    "confidence": "low",
                }
            )

    # Note: We don't suggest negative ratings automatically
    # as lack of usage doesn't mean dislike

    return suggestions


def format_analysis_summary(analysis: MealHistoryAnalysis) -> str:
    """Format the analysis as a human-readable summary."""
    lines = [
        f"## Meal History Analysis",
        f"",
        f"**Total Recipes:** {analysis.total_recipes}",
        f"",
    ]

    if analysis.favorite_cuisines:
        lines.append(f"**Favorite Cuisines:** {', '.join(analysis.favorite_cuisines)}")

    if analysis.preferred_difficulty:
        lines.append(f"**Preferred Difficulty:** {analysis.preferred_difficulty}")

    if analysis.average_prep_time:
        lines.append(f"**Average Prep Time:** {analysis.average_prep_time} minutes")

    if analysis.average_cook_time:
        lines.append(f"**Average Cook Time:** {analysis.average_cook_time} minutes")

    lines.append("")

    if analysis.cuisine_counts:
        lines.append("### Cuisine Breakdown")
        for cuisine, count in sorted(analysis.cuisine_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- {cuisine}: {count}")
        lines.append("")

    if analysis.rating_distribution:
        lines.append("### Rating Distribution")
        for rating in ["5", "4", "3", "2", "1"]:
            count = analysis.rating_distribution.get(rating, 0)
            if count > 0:
                stars = "*" * int(rating)
                lines.append(f"- {stars} ({rating}): {count} recipes")
        lines.append("")

    if analysis.suggested_updates:
        lines.append("### Suggested Preference Updates")
        for suggestion in analysis.suggested_updates:
            rating_text = {2: "love", 1: "like", -1: "dislike", -2: "hate"}.get(
                suggestion["suggested_rating"], "neutral"
            )
            lines.append(
                f"- Set **{suggestion['item']}** ({suggestion['category']}) to `{rating_text}` "
                f"({suggestion['confidence']} confidence)"
            )
            lines.append(f"  - Reason: {suggestion['reason']}")
        lines.append("")

    return "\n".join(lines)

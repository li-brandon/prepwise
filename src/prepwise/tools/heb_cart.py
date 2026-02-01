"""HEB cart automation using Playwright."""

import asyncio
import logging
import random
from urllib.parse import quote

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from prepwise.models.heb import HEBCartResult, HEBCartItem, HEBSessionStatus
from prepwise.storage.paths import HEB_SESSION_DIR, ensure_data_dir

logger = logging.getLogger(__name__)

# HEB URLs
HEB_BASE_URL = "https://www.heb.com"
HEB_SEARCH_URL = f"{HEB_BASE_URL}/search/?q="
HEB_CART_URL = f"{HEB_BASE_URL}/cart"
HEB_LOGIN_URL = f"{HEB_BASE_URL}/signin"

# Selectors (may need updates if HEB changes their site)
SELECTORS = {
    "product_tile": "[data-qe='product-tile']",
    "add_to_cart_btn": "button[data-qe='add-to-cart-btn']",
    "cart_count": "[data-qe='cart-count']",
    "search_input": "input[type='search']",
    "account_button": "[data-qe='account-button']",
    "sign_in_link": "a[href*='signin']",
    "logged_in_indicator": "[data-qe='account-menu']",
}


async def get_browser_context(headless: bool = False) -> tuple[Browser, BrowserContext]:
    """
    Get or create a persistent browser context for HEB.

    Args:
        headless: Whether to run browser in headless mode (default False for visibility)

    Returns:
        Tuple of (browser, context)
    """
    ensure_data_dir()
    HEB_SESSION_DIR.mkdir(parents=True, exist_ok=True)

    playwright = await async_playwright().start()

    # Use persistent context to maintain login state
    context = await playwright.chromium.launch_persistent_context(
        user_data_dir=str(HEB_SESSION_DIR),
        headless=headless,
        viewport={"width": 1280, "height": 800},
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    )

    return playwright, context


async def check_session_status() -> HEBSessionStatus:
    """
    Check if there's an active HEB session.

    Returns:
        HEBSessionStatus with login state information
    """
    session_exists = HEB_SESSION_DIR.exists() and any(HEB_SESSION_DIR.iterdir())

    if not session_exists:
        return HEBSessionStatus(
            logged_in=False,
            session_exists=False,
            message="No HEB session found. You'll need to log in.",
        )

    # Try to check if actually logged in by visiting HEB
    try:
        playwright, context = await get_browser_context(headless=True)
        try:
            page = context.pages[0] if context.pages else await context.new_page()

            # Go to HEB homepage
            await page.goto(HEB_BASE_URL, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Check for logged-in indicator
            logged_in = await page.locator(SELECTORS["logged_in_indicator"]).count() > 0

            if logged_in:
                return HEBSessionStatus(
                    logged_in=True, session_exists=True, message="You are logged in to HEB."
                )
            else:
                return HEBSessionStatus(
                    logged_in=False,
                    session_exists=True,
                    message="Session exists but you may need to log in again.",
                )
        finally:
            await context.close()
            await playwright.stop()

    except Exception as e:
        logger.warning(f"Error checking HEB session: {e}")
        return HEBSessionStatus(
            logged_in=False,
            session_exists=session_exists,
            message=f"Could not verify session status: {e}",
        )


async def open_heb_login() -> str:
    """
    Open HEB login page in a visible browser for interactive login.

    Returns:
        Status message
    """
    playwright, context = await get_browser_context(headless=False)

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        # Navigate to login page
        await page.goto(HEB_LOGIN_URL, timeout=30000)

        return (
            "HEB login page opened in browser. Please log in manually.\n"
            "Once logged in, your session will be saved for future use.\n"
            "Close the browser window when done, or leave it open to continue shopping."
        )
    except Exception as e:
        await context.close()
        await playwright.stop()
        raise RuntimeError(f"Failed to open HEB login: {e}")


async def add_items_to_cart(ingredients: list[str]) -> HEBCartResult:
    """
    Add ingredients to HEB cart by searching and adding products.

    Args:
        ingredients: List of ingredient strings (e.g., ["2 lbs chicken thighs", "1 onion"])

    Returns:
        HEBCartResult with summary of added/failed items
    """
    result = HEBCartResult()

    playwright, context = await get_browser_context(headless=False)

    try:
        page = context.pages[0] if context.pages else await context.new_page()

        for ingredient in ingredients:
            item_result = await _add_single_item(page, ingredient)
            result.items.append(item_result)

            if item_result.success:
                result.total_added += 1
            elif item_result.error:
                result.total_errors += 1
            else:
                result.total_not_found += 1

            # Human-like delay between items
            await asyncio.sleep(random.uniform(1.5, 3.0))

        # Try to get cart total
        try:
            await page.goto(HEB_CART_URL, timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Look for total element (selector may need adjustment)
            total_element = page.locator("[data-qe='cart-total'], .cart-total, .order-total").first
            if await total_element.count() > 0:
                total_text = await total_element.text_content()
                if total_text:
                    import re

                    match = re.search(r"\$?([\d.]+)", total_text)
                    if match:
                        result.cart_total = float(match.group(1))
        except Exception as e:
            logger.warning(f"Could not get cart total: {e}")

        return result

    except Exception as e:
        logger.error(f"Error during cart operations: {e}")
        raise
    finally:
        # Don't close context - keep session for user to review
        pass


async def _add_single_item(page: Page, ingredient: str) -> HEBCartItem:
    """
    Search for and add a single ingredient to cart.

    Args:
        page: Playwright page
        ingredient: Ingredient string

    Returns:
        HEBCartItem with result
    """
    # Clean up ingredient for search
    search_term = _clean_ingredient_for_search(ingredient)

    try:
        # Navigate to search results
        search_url = HEB_SEARCH_URL + quote(search_term)
        await page.goto(search_url, timeout=30000)

        # Wait for products to load
        try:
            await page.wait_for_selector(SELECTORS["product_tile"], timeout=10000)
        except Exception:
            # No products found
            return HEBCartItem(
                search_term=ingredient,
                success=False,
                suggestion=_get_search_suggestion(ingredient),
            )

        # Find first "Add to Cart" button
        add_btn = page.locator(SELECTORS["add_to_cart_btn"]).first

        if await add_btn.count() == 0:
            return HEBCartItem(
                search_term=ingredient,
                success=False,
                suggestion=_get_search_suggestion(ingredient),
            )

        # Get product name before clicking
        product_tile = page.locator(SELECTORS["product_tile"]).first
        product_name = None
        price = None

        try:
            name_elem = product_tile.locator("[data-qe='product-title'], .product-title").first
            if await name_elem.count() > 0:
                product_name = await name_elem.text_content()
                product_name = product_name.strip() if product_name else None

            price_elem = product_tile.locator("[data-qe='product-price'], .product-price").first
            if await price_elem.count() > 0:
                price_text = await price_elem.text_content()
                if price_text:
                    import re

                    match = re.search(r"\$?([\d.]+)", price_text)
                    if match:
                        price = float(match.group(1))
        except Exception:
            pass

        # Click add to cart
        await add_btn.click()

        # Wait a moment for cart to update
        await asyncio.sleep(1.0)

        return HEBCartItem(
            search_term=ingredient,
            product_name=product_name,
            price=price,
            success=True,
        )

    except Exception as e:
        logger.warning(f"Error adding {ingredient}: {e}")
        return HEBCartItem(
            search_term=ingredient,
            success=False,
            error=str(e),
        )


def _clean_ingredient_for_search(ingredient: str) -> str:
    """
    Clean an ingredient string for HEB search.

    Removes quantities, units, and prep instructions to get core ingredient.
    """
    import re

    # Remove common quantity patterns
    ingredient = re.sub(r"^\d+[\d./\s]*", "", ingredient)  # Leading numbers
    ingredient = re.sub(r"\([^)]*\)", "", ingredient)  # Parenthetical notes

    # Remove common units
    units = [
        "cups?",
        "tbsp?",
        "tsp?",
        "tablespoons?",
        "teaspoons?",
        "oz",
        "ounces?",
        "lbs?",
        "pounds?",
        "grams?",
        "g",
        "ml",
        "liters?",
        "quarts?",
        "pints?",
        "gallons?",
        "cloves?",
        "heads?",
        "bunche?s?",
        "cans?",
        "jars?",
        "packages?",
        "bags?",
        "boxes?",
        "containers?",
        "small",
        "medium",
        "large",
        "extra-large",
    ]
    units_pattern = r"\b(" + "|".join(units) + r")\b\.?"
    ingredient = re.sub(units_pattern, "", ingredient, flags=re.IGNORECASE)

    # Remove prep instructions
    prep_words = [
        "chopped",
        "diced",
        "minced",
        "sliced",
        "cubed",
        "crushed",
        "grated",
        "shredded",
        "melted",
        "softened",
        "fresh",
        "frozen",
        "canned",
        "dried",
        "ground",
        "optional",
        "to taste",
        "for serving",
        "divided",
    ]
    for word in prep_words:
        ingredient = re.sub(rf"\b{word}\b,?", "", ingredient, flags=re.IGNORECASE)

    # Clean up whitespace and punctuation
    ingredient = re.sub(r"\s+", " ", ingredient)
    ingredient = ingredient.strip(" ,.-")

    return ingredient


def _get_search_suggestion(ingredient: str) -> str:
    """Get a search suggestion for a failed ingredient search."""
    cleaned = _clean_ingredient_for_search(ingredient)

    # Try simplifying further
    words = cleaned.split()
    if len(words) > 2:
        # Try just the last 1-2 words (usually the main ingredient)
        return " ".join(words[-2:])

    return f"Try simpler search: {cleaned}"

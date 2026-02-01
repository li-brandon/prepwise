"""Favorite recipe websites management for PrepWise."""

from datetime import datetime, timezone
from pydantic import BaseModel, Field

from prepwise.storage.json_store import JSONStore
from prepwise.storage.paths import FAVORITE_SITES_FILE


class FavoriteSite(BaseModel):
    """A favorite recipe website."""

    url: str = Field(description="Base URL of the site (e.g., https://www.budgetbytes.com)")
    name: str = Field(description="Display name for the site")
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FavoriteSites(BaseModel):
    """Collection of favorite recipe websites."""

    sites: list[FavoriteSite] = Field(default_factory=list)

    def get_site_urls(self) -> list[str]:
        """Get list of site URLs for search queries."""
        return [site.url for site in self.sites]

    def get_site_domains(self) -> list[str]:
        """Get list of site domains for site: search queries."""
        domains = []
        for site in self.sites:
            # Extract domain from URL
            url = site.url.replace("https://", "").replace("http://", "")
            domain = url.split("/")[0]
            domains.append(domain)
        return domains


# Default favorite sites to pre-populate
DEFAULT_FAVORITE_SITES = [
    FavoriteSite(
        url="https://www.budgetbytes.com",
        name="Budget Bytes",
    ),
    FavoriteSite(
        url="https://www.allrecipes.com",
        name="AllRecipes",
    ),
    FavoriteSite(
        url="https://www.seriouseats.com",
        name="Serious Eats",
    ),
]


def get_favorite_sites_store() -> JSONStore[FavoriteSites]:
    """Get the favorite sites JSON store."""
    return JSONStore(
        FAVORITE_SITES_FILE,
        FavoriteSites,
        default_factory=lambda: FavoriteSites(sites=DEFAULT_FAVORITE_SITES.copy()),
    )


def load_favorite_sites() -> FavoriteSites:
    """Load favorite sites from storage."""
    store = get_favorite_sites_store()
    return store.load()


def save_favorite_sites(sites: FavoriteSites) -> None:
    """Save favorite sites to storage."""
    store = get_favorite_sites_store()
    store.save(sites)


def add_favorite_site(url: str, name: str) -> FavoriteSites:
    """
    Add a new favorite recipe site.

    Args:
        url: Base URL of the site (e.g., "https://www.bonappetit.com")
        name: Display name for the site

    Returns:
        Updated FavoriteSites collection
    """
    sites = load_favorite_sites()

    # Normalize URL
    url = url.strip().rstrip("/")
    if not url.startswith("http"):
        url = f"https://{url}"

    # Check if already exists
    existing_urls = [s.url.lower() for s in sites.sites]
    if url.lower() in existing_urls:
        return sites  # Already exists, no change

    # Add new site
    new_site = FavoriteSite(url=url, name=name.strip())
    sites.sites.append(new_site)

    save_favorite_sites(sites)
    return sites


def remove_favorite_site(url: str) -> FavoriteSites:
    """
    Remove a favorite recipe site.

    Args:
        url: URL of the site to remove

    Returns:
        Updated FavoriteSites collection
    """
    sites = load_favorite_sites()

    # Normalize URL for comparison
    url_normalized = url.strip().rstrip("/").lower()
    if not url_normalized.startswith("http"):
        url_normalized = f"https://{url_normalized}"

    # Filter out the matching site
    sites.sites = [s for s in sites.sites if s.url.lower() != url_normalized]

    save_favorite_sites(sites)
    return sites


def get_search_site_queries(base_query: str) -> list[str]:
    """
    Generate site-specific search queries for favorite sites.

    Args:
        base_query: The base search query (e.g., "quick chicken dinner")

    Returns:
        List of queries with site: prefixes for each favorite site
    """
    sites = load_favorite_sites()
    domains = sites.get_site_domains()

    queries = []
    for domain in domains:
        queries.append(f"site:{domain} {base_query}")

    return queries

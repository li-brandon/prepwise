"""Path constants and utilities for PrepWise data storage."""

from pathlib import Path

# Main data directory
PREPWISE_DIR = Path.home() / ".prepwise"

# File paths
PREFERENCES_FILE = PREPWISE_DIR / "preferences.json"
FAVORITE_SITES_FILE = PREPWISE_DIR / "favorite_sites.json"
SETUP_COMPLETE_FILE = PREPWISE_DIR / "setup_complete"
HEB_SESSION_DIR = PREPWISE_DIR / "heb_session"


def ensure_data_dir() -> Path:
    """Ensure the PrepWise data directory exists and return its path."""
    PREPWISE_DIR.mkdir(parents=True, exist_ok=True)
    return PREPWISE_DIR


def is_setup_complete() -> bool:
    """Check if the initial setup wizard has been completed."""
    return SETUP_COMPLETE_FILE.exists()


def mark_setup_complete() -> None:
    """Mark the initial setup as complete."""
    ensure_data_dir()
    SETUP_COMPLETE_FILE.touch()

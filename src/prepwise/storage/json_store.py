"""Generic JSON file storage utility."""

import json
from pathlib import Path
from typing import Any, TypeVar, Generic
from pydantic import BaseModel

from prepwise.storage.paths import ensure_data_dir

T = TypeVar("T", bound=BaseModel)


class JSONStore(Generic[T]):
    """Generic JSON file storage for Pydantic models."""

    def __init__(self, file_path: Path, model_class: type[T], default_factory: Any = None):
        """
        Initialize a JSON store.

        Args:
            file_path: Path to the JSON file
            model_class: Pydantic model class for (de)serialization
            default_factory: Optional callable that returns default data if file doesn't exist
        """
        self.file_path = file_path
        self.model_class = model_class
        self.default_factory = default_factory or model_class

    def load(self) -> T:
        """Load data from the JSON file, creating default if not exists."""
        ensure_data_dir()

        if not self.file_path.exists():
            return self.default_factory()

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return self.model_class.model_validate(data)
        except (json.JSONDecodeError, Exception):
            # If file is corrupted, return default
            return self.default_factory()

    def save(self, data: T) -> None:
        """Save data to the JSON file."""
        ensure_data_dir()

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data.model_dump(), f, indent=2, default=str)

    def exists(self) -> bool:
        """Check if the storage file exists."""
        return self.file_path.exists()

    def delete(self) -> bool:
        """Delete the storage file if it exists. Returns True if deleted."""
        if self.file_path.exists():
            self.file_path.unlink()
            return True
        return False

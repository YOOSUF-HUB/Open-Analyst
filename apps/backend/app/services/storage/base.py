from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    @abstractmethod
    def save(self, source_path: Path, storage_filename: str) -> str:
        """Save a file and return the relative storage key."""

    @abstractmethod
    def get_path(self, storage_key: str) -> Path:
        """Resolve a storage key to a readable filesystem path."""

    @abstractmethod
    def delete(self, storage_key: str) -> None:
        """Delete a stored file."""

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """Check whether a stored file exists."""

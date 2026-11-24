import logging
import shutil
from pathlib import Path

from app.services.storage.base import StorageBackend

logger = logging.getLogger(__name__)


class LocalStorage(StorageBackend):
    def __init__(self, base_dir: Path) -> None:
        self._base = base_dir
        self._base.mkdir(parents=True, exist_ok=True)

    def save(self, source_path: Path, storage_filename: str) -> str:
        dest = self._base / storage_filename
        shutil.copy2(source_path, dest)
        logger.debug("Stored file: %s", dest)
        return storage_filename

    def get_path(self, storage_key: str) -> Path:
        # Prevent path traversal: only allow bare filename
        name = Path(storage_key).name
        if name != storage_key:
            raise ValueError(f"Invalid storage key: {storage_key!r}")
        return self._base / name

    def delete(self, storage_key: str) -> None:
        path = self.get_path(storage_key)
        if path.exists():
            path.unlink()
            logger.debug("Deleted stored file: %s", path)

    def exists(self, storage_key: str) -> bool:
        return self.get_path(storage_key).exists()


_storage: LocalStorage | None = None


def get_storage() -> LocalStorage:
    global _storage
    if _storage is None:
        from app.config import get_settings

        settings = get_settings()
        base = Path(settings.upload_dir)
        _storage = LocalStorage(base)
    return _storage

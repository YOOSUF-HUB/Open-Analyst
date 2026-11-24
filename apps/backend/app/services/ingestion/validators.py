import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

# Magic bytes for file type validation
CSV_PRINTABLE_THRESHOLD = 0.90  # 90% of bytes must be printable ASCII for CSV
XLSX_MAGIC = b"PK\x03\x04"  # ZIP magic (XLSX is a ZIP archive)

_MAX_FILENAME_LENGTH = 255


def validate_filename(filename: str) -> None:
    """Reject filenames with null bytes or lengths exceeding the DB column limit."""
    if "\x00" in filename:
        raise ValueError("Filename contains invalid characters.")
    if len(filename) > _MAX_FILENAME_LENGTH:
        raise ValueError(f"Filename is too long (maximum {_MAX_FILENAME_LENGTH} characters).")


def validate_extension(filename: str) -> str:
    """Return the lowercase extension or raise ValueError."""
    if not filename:
        raise ValueError("Filename is empty.")
    dot = filename.rfind(".")
    if dot < 0:
        raise ValueError("File has no extension.")
    ext = filename[dot:].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )
    return ext


def validate_file_size(size_bytes: int, max_bytes: int) -> None:
    if size_bytes == 0:
        raise ValueError("File is empty.")
    if size_bytes > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        raise ValueError(f"File exceeds maximum size of {max_mb:.0f} MB.")


def validate_csv_signature(header_bytes: bytes) -> None:
    """Validate that the file looks like a CSV (text, not binary)."""
    if not header_bytes:
        raise ValueError("File is empty.")
    # Strip UTF-8 BOM if present
    sample = header_bytes.lstrip(b"\xef\xbb\xbf")
    if not sample:
        raise ValueError("File is empty after BOM removal.")
    # Check that enough bytes are printable text
    printable = sum(1 for b in sample if 0x09 <= b <= 0x0D or 0x20 <= b <= 0x7E)
    if len(sample) > 0 and printable / len(sample) < CSV_PRINTABLE_THRESHOLD:
        raise ValueError("File does not appear to be a valid CSV (binary content detected).")


def validate_xlsx_signature(header_bytes: bytes) -> None:
    """Validate XLSX magic bytes (ZIP archive header)."""
    if len(header_bytes) < 4:
        raise ValueError("File is too small to be a valid XLSX.")
    if not header_bytes.startswith(XLSX_MAGIC):
        raise ValueError("File does not appear to be a valid XLSX workbook.")


def validate_file_contents(data: bytes, ext: str) -> None:
    """Validate file signature based on detected extension."""
    header = data[:512]
    if ext == ".csv":
        validate_csv_signature(header)
    elif ext == ".xlsx":
        validate_xlsx_signature(header)
    else:
        raise ValueError(f"No signature validator for extension {ext!r}.")

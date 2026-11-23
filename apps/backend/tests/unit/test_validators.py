import pytest

from app.services.ingestion.validators import (
    validate_csv_signature,
    validate_extension,
    validate_file_contents,
    validate_file_size,
    validate_xlsx_signature,
)

XLSX_MAGIC = b"PK\x03\x04" + b"\x00" * 100


def test_valid_csv_extension():
    assert validate_extension("data.csv") == ".csv"


def test_valid_xlsx_extension():
    assert validate_extension("book.xlsx") == ".xlsx"


def test_uppercase_extension_normalised():
    assert validate_extension("DATA.CSV") == ".csv"


def test_unsupported_extension_raises():
    with pytest.raises(ValueError, match="Unsupported"):
        validate_extension("data.xls")


def test_no_extension_raises():
    with pytest.raises(ValueError):
        validate_extension("noext")


def test_empty_filename_raises():
    with pytest.raises(ValueError):
        validate_extension("")


def test_file_size_zero_raises():
    with pytest.raises(ValueError, match="empty"):
        validate_file_size(0, 1024)


def test_file_size_exceeds_raises():
    with pytest.raises(ValueError, match="exceeds"):
        validate_file_size(1025, 1024)


def test_file_size_ok():
    validate_file_size(512, 1024)  # should not raise


def test_csv_signature_valid():
    validate_csv_signature(b"col1,col2\n1,2\n")  # should not raise


def test_csv_signature_binary_raises():
    # Mostly null bytes = binary content
    with pytest.raises(ValueError, match="binary"):
        validate_csv_signature(bytes(range(256)))


def test_csv_signature_empty_raises():
    with pytest.raises(ValueError, match="empty"):
        validate_csv_signature(b"")


def test_xlsx_signature_valid():
    validate_xlsx_signature(XLSX_MAGIC)  # should not raise


def test_xlsx_signature_invalid_raises():
    with pytest.raises(ValueError, match="valid XLSX"):
        validate_xlsx_signature(b"not a zip file header here")


def test_validate_file_contents_csv():
    validate_file_contents(b"a,b\n1,2\n", ".csv")  # should not raise


def test_validate_file_contents_xlsx():
    validate_file_contents(XLSX_MAGIC, ".xlsx")  # should not raise


def test_validate_file_contents_unknown_ext_raises():
    with pytest.raises(ValueError):
        validate_file_contents(b"anything", ".txt")

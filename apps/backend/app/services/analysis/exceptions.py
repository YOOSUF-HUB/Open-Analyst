"""
Exceptions raised by the Phase 2 query builder.

All are subclasses of ValueError so callers can catch the base class when
they don't need to distinguish the specific error type.
"""


class QueryBuilderError(ValueError):
    """Base exception for all query construction errors."""


class UnknownColumnError(QueryBuilderError):
    """A requested column does not exist in the dataset profile."""


class ColumnTypeError(QueryBuilderError):
    """An operator or function is incompatible with the column's logical type."""


class MissingValueError(QueryBuilderError):
    """An operator that requires a value received None."""


class InvalidAliasError(QueryBuilderError):
    """An aggregation alias is empty or exceeds the maximum length."""


class DuplicateAliasError(QueryBuilderError):
    """Two aggregation specs resolve to the same output alias."""


class ResourceLimitError(QueryBuilderError):
    """A resource limit was exceeded."""

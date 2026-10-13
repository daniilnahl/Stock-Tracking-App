"""Local domain validation errors."""


class DomainValidationError(ValueError):
    """A domain input does not satisfy its local contract."""


class SnapshotCurrencyUnavailableError(DomainValidationError):
    """A valuation row lacks required currency evidence."""


class SnapshotCurrencyMismatchError(DomainValidationError):
    """A valuation row's asserted currency differs from the aggregate currency."""

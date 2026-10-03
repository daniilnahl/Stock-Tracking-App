"""Shared credential boundary for the legacy application entry points."""

from dataclasses import dataclass, field
import logging
import os

import dotenv


logger = logging.getLogger(__name__)


class ConfigurationError(ValueError):
    """A safe, user-facing configuration failure."""


@dataclass(frozen=True)
class Configuration:
    api_key: str | None = field(default=None, repr=False)


def load_configuration() -> Configuration:
    """Load optional dotenv without overriding process values of the same name.

    The canonical name wins across sources; legacy fallback is used only when
    FMP_API_KEY is absent, never when it is explicitly blank.
    """
    try:
        dotenv.load_dotenv()
    except Exception:
        # Third-party exceptions may contain file contents or credentials.
        logger.error("Unable to load local credential configuration.")
        raise ConfigurationError("Unable to load local credential configuration.") from None
    return Configuration(os.getenv("FMP_API_KEY", os.getenv("MY_API_KEY")))


def require_api_key(api_key: str | None) -> str:
    """Validate before network work without including the supplied value."""
    if api_key is None or not api_key.strip():
        raise ConfigurationError(
            "Set FMP_API_KEY in your environment or local .env before making requests."
        )
    return api_key

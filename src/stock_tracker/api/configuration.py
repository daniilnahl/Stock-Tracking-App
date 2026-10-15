"""Explicit local launch configuration; metadata checks never open state."""

from dataclasses import dataclass, field
import os
from pathlib import Path
import stat

from .access import validate_token


class ApiConfigurationError(ValueError):
    def __init__(self):
        super().__init__("Local API configuration is invalid. Check the required token and four distinct file paths.")


_ISSUED = object()


@dataclass(frozen=True, slots=True, init=False)
class ApiConfiguration:
    database: Path
    history_cache: Path
    menu_legacy: Path
    evaluation_legacy: Path
    token: str = field(repr=False)
    enable_history: bool = False
    _seal: object = field(repr=False)
    _issued_paths: tuple[Path, ...] = field(repr=False)

    def __init__(self, *args, **kwargs):
        raise ApiConfigurationError()


def require_validated_configuration(configuration):
    """Pure check of loader issuance; never repeat filesystem resolution."""
    try:
        if not isinstance(configuration, ApiConfiguration) or configuration._seal is not _ISSUED:
            raise ApiConfigurationError()
        paths = (configuration.database, configuration.history_cache, configuration.menu_legacy, configuration.evaluation_legacy)
        if paths != configuration._issued_paths or any(not isinstance(path, Path) or not path.is_absolute() for path in paths):
            raise ApiConfigurationError()
        if len({os.path.normcase(str(path)) for path in paths}) != 4 or type(configuration.enable_history) is not bool:
            raise ApiConfigurationError()
        if configuration.token is None:
            raise ApiConfigurationError()
        validate_token(configuration.token)
    except (AttributeError, TypeError, ValueError):
        raise ApiConfigurationError() from None


def _resolved_file(value: str) -> Path:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ApiConfigurationError()
    path = Path(value)
    if os.name == "nt":
        # Win32 trims trailing dots/spaces, recognizes devices and streams, and
        # permits drive-relative spelling. These do not identify clear files.
        if value.replace("/", "\\").startswith(("\\\\?\\", "\\\\.\\")) or (path.drive and not path.is_absolute()):
            raise ApiConfigurationError()
        for part in path.parts[1:] if path.anchor else path.parts:
            if part not in (".", "..") and (part.endswith((".", " ")) or ":" in part or Path(part).is_reserved()):
                raise ApiConfigurationError()
    # Check original directory entries as well: resolving a dangling symlink
    # with strict=False otherwise silently turns it into a new missing target.
    for candidate in (path, *path.parents):
        try:
            information = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(information.st_mode) or (
                getattr(information, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            # Windows junctions are reparse points, but not S_ISLNK. A
            # dangling junction must not become a silently new missing path.
            candidate.resolve(strict=True)
    resolved = path.resolve(strict=False)
    try:
        mode = resolved.stat().st_mode
    except FileNotFoundError:
        # Missing directories stay missing. Existing ancestors must really be
        # directories, rather than an ambiguous file-as-parent spelling.
        for parent in resolved.parents:
            try:
                parent_mode = parent.stat().st_mode
            except FileNotFoundError:
                continue
            if not stat.S_ISDIR(parent_mode):
                raise ApiConfigurationError()
            break
    else:
        if not stat.S_ISREG(mode):
            raise ApiConfigurationError()
    return resolved


def load_api_configuration(*, database: str, history_cache: str, menu_legacy: str,
                           evaluation_legacy: str, enable_history: bool = False) -> ApiConfiguration:
    """Resolve each explicit file once; process environment supplies only token."""
    try:
        if type(enable_history) is not bool:
            raise ApiConfigurationError()
        token = os.environ.get("STOCK_TRACKER_API_TOKEN")
        if token is None:
            raise ApiConfigurationError()
        validate_token(token)
        paths = tuple(_resolved_file(value) for value in (database, history_cache, menu_legacy, evaluation_legacy))
        names = [os.path.normcase(str(path)) for path in paths]
        if len(set(names)) != 4:
            raise ApiConfigurationError()
        # stat/samefile follows symlinks and identifies existing hard links.
        for index, first in enumerate(paths):
            for second in paths[index + 1:]:
                try:
                    same = first.samefile(second)
                except FileNotFoundError:
                    same = False
                if same:
                    raise ApiConfigurationError()
        configuration = object.__new__(ApiConfiguration)
        for name, value in zip(("database", "history_cache", "menu_legacy", "evaluation_legacy"), paths):
            object.__setattr__(configuration, name, value)
        for name, value in (("token", token), ("enable_history", enable_history), ("_seal", _ISSUED), ("_issued_paths", paths)):
            object.__setattr__(configuration, name, value)
        require_validated_configuration(configuration)
        return configuration
    except (OSError, RuntimeError, ValueError):
        raise ApiConfigurationError() from None

from importlib_metadata import PackageNotFoundError  # pragma: no cover
from importlib_metadata import version

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = "fritz-dect-mail-extract"
    __version__ = version(dist_name)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

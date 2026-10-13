"""Tea CLI — control the Tea multi-livestream platform from your terminal."""
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("tea-cli")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

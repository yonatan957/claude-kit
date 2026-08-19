"""One service per command, each driving the sources list."""

from .install_service import install
from .search_service import search
from .uninstall_service import uninstall

__all__ = ["search", "install", "uninstall"]

"""One service per command, each driving the sources list."""

from .install_service import InstallService
from .search_service import SearchService
from .uninstall_service import UninstallService

__all__ = ["SearchService", "InstallService", "UninstallService"]

"""One service per command, each driving the sources list."""

from claude_kit.services.install_service import install
from claude_kit.services.search_service import search
from claude_kit.services.uninstall_service import uninstall

__all__ = ["search", "install", "uninstall"]

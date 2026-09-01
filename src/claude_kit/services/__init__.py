"""One service per command, each driving the sources list."""

from claude_kit.services.init_service import CLAUDE_CODE, InitResult, init
from claude_kit.services.install_service import install
from claude_kit.services.list_service import get_installed_components
from claude_kit.services.search_service import search
from claude_kit.services.status_service import get_state
from claude_kit.services.uninstall_service import uninstall

__all__ = [
    "CLAUDE_CODE",
    "InitResult",
    "init",
    "search",
    "install",
    "uninstall",
    "get_installed_components",
    "get_state",
]

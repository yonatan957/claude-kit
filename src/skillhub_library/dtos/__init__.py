"""One request object per command, each knowing the argv it turns into.

There is no generic keyword-to-flag translator here on purpose. Every flag the
CLI understands is named by exactly one field on exactly one request, so the
set of arguments this library can ever produce is the set written down in this
package -- a new CLI flag has to be added deliberately, and a typo cannot
invent one.
"""

from .base import Request
from .install import InstallRequest
from .search import SearchRequest
from .uninstall import UninstallRequest

__all__ = ["Request", "SearchRequest", "InstallRequest", "UninstallRequest"]

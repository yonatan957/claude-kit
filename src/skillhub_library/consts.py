"""Values this library fixes rather than the caller, named in one place.

Each of these is referred to from more than one spot -- a name, a default, an
environment variable read once and quoted again in an error message -- so
spelling any of them out at the point of use would mean changing the same
string in several files at once.

The environment is read here, at import, and nowhere else: a module that has to
reach for ``os.environ`` mid-call is a module whose answer can change between
two calls that look identical. The cost is that setting ``$SKILLHUB_BIN`` after
importing this package has no effect.
"""

import os

__all__ = ["BINARIES", "BINARY_ENV_VAR", "INSTALL_HINT", "REQUEST_TIMEOUT"]

#: Environment variable holding one explicit path to the CLI, for when it is
#: installed somewhere :func:`shutil.which` will not find it.
BINARY_ENV_VAR = "SKILLHUB_BIN"

_override = os.environ.get(BINARY_ENV_VAR)

#: Executable names to try, in order -- add a fallback here if the CLI is ever
#: published under another name. An override does not join the list, it replaces
#: it: naming a path and then falling back to ``$PATH`` would hide a typo in it.
BINARIES: tuple[str, ...] = (_override,) if _override else ("skillhub",)

#: How to get the CLI, quoted back when locating it fails.
INSTALL_HINT = "npm install -g @astron-team/skillhub"

#: Seconds to wait for a single CLI invocation to finish before giving up. It
#: bounds one ``subprocess.run``, not a whole session: an install that has to
#: download a package is the slowest thing this wraps.
REQUEST_TIMEOUT = 120.0

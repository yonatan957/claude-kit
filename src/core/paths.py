"""Local filesystem path resolvers for claude-kit's own state and the developer's
Claude Code environment. Pure functions only — no I/O (Principle I): callers are
responsible for creating/reading/writing whatever these paths point to.
"""

from pathlib import Path


def home_dir() -> Path:
    return Path.home()


def claude_kit_dir() -> Path:
    return home_dir() / ".claude-kit"


def claude_kit_repo_dir() -> Path:
    return home_dir() / ".claude-kit-repo"


def claude_dir() -> Path:
    return home_dir() / ".claude"


def skills_dir() -> Path:
    return claude_dir() / "skills"


def agents_dir() -> Path:
    return claude_dir() / "agents"


def claude_settings_path() -> Path:
    return claude_dir() / "settings.json"


def claude_md_path() -> Path:
    return claude_dir() / "CLAUDE.md"


def env_dir() -> Path:
    return claude_kit_dir() / "env.d"


def secret_file_path(component_name: str) -> Path:
    return env_dir() / f"{component_name}.env"


def installed_json_path() -> Path:
    return claude_kit_dir() / "installed.json"


def state_json_path() -> Path:
    return claude_kit_dir() / "state.json"


def registry_json_path() -> Path:
    return claude_kit_repo_dir() / "registry.json"

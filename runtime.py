"""Shared configuration: provider resolution and system prompt (CLI + server)."""

from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Literal

import keys as keys_mod

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

SYSTEM_PROMPT = (
    "You are an expert software engineer and coding assistant. "
    "Help users by reading files, writing code, running commands, and explaining concepts. "
    "Always read relevant files before editing them to understand the existing context. "
    "Be concise and direct. Prefer making changes incrementally."
)

# Pricing per million tokens: (input, output, cache_read, cache_write)
MODEL_COSTS: dict[str, tuple[float, float, float, float]] = {
    "claude-opus-4-7":          (15.00, 75.00, 1.50,  18.75),
    "claude-sonnet-4-6":        ( 3.00, 15.00, 0.30,   3.75),
    "claude-haiku-4-5-20251001":( 0.80,  4.00, 0.08,   1.00),
    "llama-3.3-70b-versatile":  ( 0.59,  0.79, 0.00,   0.00),
    "gemini-2.0-flash":         ( 0.10,  0.40, 0.00,   0.00),
}

SESSIONS_DIR = Path(".mini-claude-sessions")


class ConfigurationError(Exception):
    """Invalid or missing API configuration."""


def confirm_mode() -> bool:
    """Whether the CLI should prompt before destructive tool actions."""
    return os.environ.get("MINI_CODE_CONFIRM", "").strip().lower() in ("1", "true", "yes")


def max_agent_rounds() -> int:
    """Cap API round-trips in the tool loop (each model completion counts as one round)."""
    raw = os.environ.get("MINI_CODE_MAX_TOOL_ROUNDS", "64").strip()
    try:
        n = int(raw)
    except ValueError:
        return 64
    return max(1, min(n, 10_000))


# ─── Token tracking ───────────────────────────────────────────────────────────

class TokenTracker:
    """Accumulates token usage across a session."""

    def __init__(self):
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cache_read_tokens = 0
        self.cache_write_tokens = 0
        self.total_tokens = 0
        self.api_calls = 0

    def add(
        self,
        prompt: int,
        completion: int,
        cache_read: int = 0,
        cache_write: int = 0,
    ) -> None:
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.cache_read_tokens += cache_read
        self.cache_write_tokens += cache_write
        self.total_tokens += prompt + completion
        self.api_calls += 1

    def usd_cost(self, model: str = "") -> float:
        costs = MODEL_COSTS.get(model)
        if not costs:
            return 0.0
        inp, out, cr, cw = costs
        return (
            self.prompt_tokens      * inp / 1_000_000
            + self.completion_tokens * out / 1_000_000
            + self.cache_read_tokens * cr  / 1_000_000
            + self.cache_write_tokens * cw / 1_000_000
        )

    def summary(self, model: str = "") -> str:
        cost = self.usd_cost(model)
        cost_str = f" ≈ ${cost:.4f}" if cost > 0 else ""
        cache_str = ""
        if self.cache_read_tokens or self.cache_write_tokens:
            cache_str = (
                f" cache_read={self.cache_read_tokens:,}"
                f" cache_write={self.cache_write_tokens:,}"
            )
        return (
            f"[tokens] prompt={self.prompt_tokens:,} completion={self.completion_tokens:,} "
            f"total={self.total_tokens:,} calls={self.api_calls}{cache_str}{cost_str}"
        )


# ─── Session persistence ──────────────────────────────────────────────────────

def save_session(name: str, messages: list) -> Path:
    """Save conversation messages to a JSON file."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = SESSIONS_DIR / f"{name}.json"
    path.write_text(json.dumps(messages, indent=2, default=str), encoding="utf-8")
    return path


def load_session(name: str) -> list | None:
    """Load conversation messages from a JSON file. Returns None if not found."""
    path = SESSIONS_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_sessions() -> list[str]:
    """List saved session names."""
    if not SESSIONS_DIR.exists():
        return []
    return sorted(p.stem for p in SESSIONS_DIR.glob("*.json"))


# ─── Context window management ────────────────────────────────────────────────

# Rough per-model context limits (tokens)
MODEL_CONTEXT_LIMITS = {
    "llama-3.3-70b-versatile": 128_000,
    "gemini-2.0-flash": 1_000_000,
    "claude-sonnet-4-6": 200_000,
}
DEFAULT_CONTEXT_LIMIT = 128_000


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars per token for English)."""
    return len(text) // 4


def estimate_messages_tokens(messages: list) -> int:
    """Estimate total tokens across all messages."""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict):
                    total += estimate_tokens(str(part))
                else:
                    total += estimate_tokens(str(part))
    return total


def truncate_messages(messages: list, model: str = "") -> list:
    """Truncate oldest messages (keeping the first user message) if over 75% of context limit."""
    limit = MODEL_CONTEXT_LIMITS.get(model, DEFAULT_CONTEXT_LIMIT)
    threshold = int(limit * 0.75)
    current = estimate_messages_tokens(messages)
    if current <= threshold:
        return messages
    # Keep first message + trim from the start of middle messages
    while len(messages) > 2 and estimate_messages_tokens(messages) > threshold:
        messages.pop(1)
    return messages


def _run_git(*args: str) -> str:
    """Run a git command and return stdout, or empty string on failure."""
    try:
        r = subprocess.run(
            ["git", *args], capture_output=True, text=True, timeout=3
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def _load_memory_files() -> str:
    """Collect CLAUDE.md files from cwd up to home and ~/.claude/CLAUDE.md."""
    sections: list[str] = []
    cwd = Path.cwd().resolve()
    home = Path.home().resolve()

    current = cwd
    visited: list[Path] = []
    while True:
        visited.append(current)
        if current == home:
            break
        parent = current.parent
        if parent == current:
            break
        current = parent

    for directory in visited:
        for name in ("CLAUDE.md", ".claude.md"):
            p = directory / name
            if p.exists():
                label = "~" / p.relative_to(home) if p.is_relative_to(home) else p
                try:
                    content = p.read_text(encoding="utf-8").strip()
                    if content:
                        sections.append(f"## {label}\n{content}")
                except OSError:
                    pass

    user_claude = home / ".claude" / "CLAUDE.md"
    if user_claude.exists() and user_claude not in {directory / "CLAUDE.md" for directory in visited}:
        try:
            content = user_claude.read_text(encoding="utf-8").strip()
            if content:
                sections.append(f"## ~/.claude/CLAUDE.md\n{content}")
        except OSError:
            pass

    if not sections:
        return ""
    return "# Project Memory (CLAUDE.md files)\n\n" + "\n\n".join(sections)


def load_system_prompt() -> str:
    """Build the system prompt with live environment context and CLAUDE.md memory."""
    env_lines: list[str] = [
        f"Working directory: {Path.cwd()}",
        f"OS: {platform.system()} {platform.release()}",
        f"Shell: {os.environ.get('SHELL', os.environ.get('COMSPEC', 'unknown'))}",
    ]

    branch = _run_git("branch", "--show-current")
    if branch:
        env_lines.append(f"Git branch: {branch}")
        status = _run_git("status", "--short")
        if status:
            env_lines.append(f"Git status:\n{status}")
        log = _run_git("log", "--oneline", "-5")
        if log:
            env_lines.append(f"Recent commits:\n{log}")

    parts = [SYSTEM_PROMPT, "# Environment\n" + "\n".join(env_lines)]

    memory = _load_memory_files()
    if memory:
        parts.append(memory)

    return "\n\n".join(parts)


def openai_configs_for(provider: str) -> list[tuple[str, str, str]]:
    """List of (base_url, api_key, model) for OpenAI-compatible providers."""
    groq_keys = keys_mod.collect_api_keys("GROQ_API_KEY", "GROQ_API_KEYS")
    gemini_keys = keys_mod.collect_api_keys("GEMINI_API_KEY", "GEMINI_API_KEYS")
    groq_model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    gemini_model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    if provider == "groq":
        return [(GROQ_BASE_URL, k, groq_model) for k in groq_keys]
    if provider == "gemini":
        return [(GEMINI_OPENAI_BASE_URL, k, gemini_model) for k in gemini_keys]

    configs: list[tuple[str, str, str]] = []
    for k in groq_keys:
        configs.append((GROQ_BASE_URL, k, groq_model))
    for k in gemini_keys:
        configs.append((GEMINI_OPENAI_BASE_URL, k, gemini_model))
    return configs


def resolve_backend() -> tuple[Literal["openai", "anthropic"], list[tuple[str, str, str]] | None]:
    """
    Returns (backend, openai_configs). openai_configs is set only when backend == 'openai'.
    Raises ConfigurationError if nothing is configured.
    """
    raw = os.environ.get("MINI_CODE_PROVIDER", "auto").strip().lower()
    if raw not in ("auto", "groq", "gemini", "anthropic"):
        raise ConfigurationError(f"Unknown MINI_CODE_PROVIDER={raw!r}. Use auto|groq|gemini|anthropic.")

    if raw == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise ConfigurationError("ANTHROPIC_API_KEY is not set.")
        return "anthropic", None

    configs = openai_configs_for(raw)
    if raw in ("groq", "gemini"):
        if not configs:
            key_hint = "GROQ_API_KEY or GROQ_API_KEYS" if raw == "groq" else "GEMINI_API_KEY or GEMINI_API_KEYS"
            raise ConfigurationError(f"{key_hint} not set for MINI_CODE_PROVIDER={raw}.")
        return "openai", configs

    if configs:
        return "openai", configs
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic", None

    raise ConfigurationError(
        "No API keys found. Set GROQ_API_KEY / GROQ_API_KEYS and/or "
        "GEMINI_API_KEY / GEMINI_API_KEYS, or ANTHROPIC_API_KEY with MINI_CODE_PROVIDER=auto, "
        "or MINI_CODE_PROVIDER=anthropic with ANTHROPIC_API_KEY."
    )

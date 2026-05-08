"""Shared configuration: provider resolution and system prompt (CLI + server)."""

from __future__ import annotations

import os
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


class ConfigurationError(Exception):
    """Invalid or missing API configuration."""


def max_agent_rounds() -> int:
    """Cap API round-trips in the tool loop (each model completion counts as one round)."""
    raw = os.environ.get("MINI_CODE_MAX_TOOL_ROUNDS", "64").strip()
    try:
        n = int(raw)
    except ValueError:
        return 64
    return max(1, min(n, 10_000))


def load_system_prompt() -> str:
    claude_md = Path("CLAUDE.md")
    if claude_md.exists():
        extra = claude_md.read_text(encoding="utf-8")
        return f"{SYSTEM_PROMPT}\n\n# Project Context (CLAUDE.md)\n{extra}"
    return SYSTEM_PROMPT


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

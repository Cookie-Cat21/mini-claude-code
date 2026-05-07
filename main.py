#!/usr/bin/env python3
"""mini-claude-code: a minimal AI coding assistant (Claude, Groq, or Gemini)."""

import os
import sys
from pathlib import Path

import anthropic

import keys as keys_mod
from agent import run_agent_anthropic
from agent_openai import run_agent_openai

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

BANNER = """\033[36m
  ╔══════════════════════════════════════╗
  ║         mini-claude-code             ║
  ║   Groq · Gemini · Claude (tools)     ║
  ╚══════════════════════════════════════╝
\033[0m"""

SYSTEM_PROMPT = (
    "You are an expert software engineer and coding assistant. "
    "Help users by reading files, writing code, running commands, and explaining concepts. "
    "Always read relevant files before editing them to understand the existing context. "
    "Be concise and direct. Prefer making changes incrementally."
)


def load_system_prompt() -> str:
    claude_md = Path("CLAUDE.md")
    if claude_md.exists():
        extra = claude_md.read_text(encoding="utf-8")
        return f"{SYSTEM_PROMPT}\n\n# Project Context (CLAUDE.md)\n{extra}"
    return SYSTEM_PROMPT


def _openai_configs(provider: str) -> list[tuple[str, str, str]]:
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


def _resolve_mode() -> tuple[str, list | None]:
    """
    Returns (backend, extra) where backend is 'openai' | 'anthropic',
    and extra is openai configs list or None.
    """
    raw = os.environ.get("MINI_CODE_PROVIDER", "auto").strip().lower()
    if raw not in ("auto", "groq", "gemini", "anthropic"):
        print(f"\033[31mUnknown MINI_CODE_PROVIDER={raw!r}. Use auto|groq|gemini|anthropic.\033[0m")
        sys.exit(1)

    if raw == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("\033[31mError: ANTHROPIC_API_KEY is not set.\033[0m")
            sys.exit(1)
        return "anthropic", None

    configs = _openai_configs(raw)
    if raw in ("groq", "gemini"):
        if not configs:
            key_hint = "GROQ_API_KEY or GROQ_API_KEYS" if raw == "groq" else "GEMINI_API_KEY or GEMINI_API_KEYS"
            print(f"\033[31mError: {key_hint} not set for MINI_CODE_PROVIDER={raw}.\033[0m")
            sys.exit(1)
        return "openai", configs

    # auto
    if configs:
        return "openai", configs
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic", None

    print(
        "\033[31mError: No API keys found.\033[0m\n"
        "  Set one of:\n"
        "    GROQ_API_KEY or comma-separated GROQ_API_KEYS\n"
        "    GEMINI_API_KEY or comma-separated GEMINI_API_KEYS\n"
        "    ANTHROPIC_API_KEY (used when no Groq/Gemini keys and MINI_CODE_PROVIDER=auto)\n"
        "  Or set MINI_CODE_PROVIDER=anthropic and ANTHROPIC_API_KEY."
    )
    sys.exit(1)


def main() -> None:
    backend, openai_configs = _resolve_mode()
    system = load_system_prompt()
    messages: list = []

    print(BANNER)
    if backend == "openai":
        n_groq = len(keys_mod.collect_api_keys("GROQ_API_KEY", "GROQ_API_KEYS"))
        n_gem = len(keys_mod.collect_api_keys("GEMINI_API_KEY", "GEMINI_API_KEYS"))
        print(f"  \033[32mBackend:\033[0m OpenAI-compatible ({len(openai_configs)} key slot(s); {n_groq} Groq, {n_gem} Gemini)")
    else:
        print("  \033[32mBackend:\033[0m Anthropic Claude")

    if Path("CLAUDE.md").exists():
        print("  \033[32m✓\033[0m Loaded CLAUDE.md\n")

    print("  Type your request and press Enter. Ctrl+C or 'exit' to quit.\n")

    anthropic_client: anthropic.Anthropic | None = None
    if backend == "anthropic":
        anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    while True:
        try:
            user_input = input("\033[1mYou:\033[0m ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nBye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "q"):
            print("Bye!")
            break

        messages.append({"role": "user", "content": user_input})

        label = "Assistant" if backend == "openai" else "Claude"
        print(f"\n\033[1m{label}:\033[0m ", end="", flush=True)
        try:
            if backend == "anthropic" and anthropic_client:
                response = run_agent_anthropic(anthropic_client, messages, system)
            else:
                response = run_agent_openai(openai_configs or [], messages, system)
            print(response)
        except anthropic.APIError as e:
            print(f"\n\033[31mAPI error: {e}\033[0m")
            messages.pop()
        except Exception as e:
            print(f"\n\033[31mError: {e}\033[0m")
            messages.pop()

        print()


if __name__ == "__main__":
    main()

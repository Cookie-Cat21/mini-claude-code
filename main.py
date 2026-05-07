#!/usr/bin/env python3
"""mini-claude-code: a minimal AI coding assistant powered by Claude."""

import os
import sys
from pathlib import Path

import anthropic

from agent import run_agent

BANNER = """\033[36m
  ╔══════════════════════════════════════╗
  ║         mini-claude-code             ║
  ║    AI coding assistant in ~150 LOC   ║
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


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\033[31mError: ANTHROPIC_API_KEY environment variable is not set.\033[0m")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    system = load_system_prompt()
    messages: list = []

    print(BANNER)

    if Path("CLAUDE.md").exists():
        print("  \033[32m✓\033[0m Loaded CLAUDE.md\n")

    print("  Type your request and press Enter. Ctrl+C or 'exit' to quit.\n")

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

        print("\n\033[1mClaude:\033[0m ", end="", flush=True)
        try:
            response = run_agent(client, messages, system)
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

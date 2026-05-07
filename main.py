#!/usr/bin/env python3
"""mini-claude-code: a minimal AI coding assistant (Claude, Groq, or Gemini)."""

import os
import sys
from pathlib import Path

import anthropic

import keys as keys_mod
from agent import run_agent_anthropic
from agent_openai import run_agent_openai
from runtime import ConfigurationError, load_system_prompt, resolve_backend

BANNER = """\033[36m
  ╔══════════════════════════════════════╗
  ║         mini-claude-code             ║
  ║   Groq · Gemini · Claude (tools)     ║
  ╚══════════════════════════════════════╝
\033[0m"""


def main() -> None:
    try:
        backend, openai_configs = resolve_backend()
    except ConfigurationError as e:
        print(f"\033[31m{e}\033[0m")
        sys.exit(1)

    system = load_system_prompt()
    messages: list = []

    print(BANNER)
    if backend == "openai":
        n_groq = len(keys_mod.collect_api_keys("GROQ_API_KEY", "GROQ_API_KEYS"))
        n_gem = len(keys_mod.collect_api_keys("GEMINI_API_KEY", "GEMINI_API_KEYS"))
        print(f"  \033[32mBackend:\033[0m OpenAI-compatible ({len(openai_configs or [])} key slot(s); {n_groq} Groq, {n_gem} Gemini)")
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

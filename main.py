#!/usr/bin/env python3
"""mini-claude-code: a minimal AI coding assistant (Claude, Groq, or Gemini)."""

import os
import sys
from pathlib import Path

import anthropic

import keys as keys_mod
from agent import MODEL as ANTHROPIC_MODEL
from agent import compact_messages, run_agent_anthropic
from agent_openai import run_agent_openai
from runtime import (
    ConfigurationError,
    TokenTracker,
    confirm_mode,
    list_sessions,
    load_session,
    load_system_prompt,
    resolve_backend,
    save_session,
)
from tools import set_confirm_callback

BANNER = """\033[36m
  ╔══════════════════════════════════════╗
  ║         mini-claude-code             ║
  ║   Groq · Gemini · Claude (tools)     ║
  ╚══════════════════════════════════════╝
\033[0m"""

HELP_TEXT = """\033[90m
  Commands:
    /help                Show this help
    /clear               Reset conversation history
    /save <name>         Save current session
    /load <name>         Load a saved session
    /sessions            List saved sessions
    /model <name>        Switch model (Groq/Gemini only)
    /tokens              Show token usage for this session
    /cost                Show estimated USD cost for this session
    /paste               Enter multi-line input mode (end with empty line)
    /compact             Summarize and compact conversation history (AI-powered)
    exit | quit | q      Exit the program

  Environment:
    MINI_CODE_CONFIRM=1  Prompt before destructive actions (write/edit/bash)
\033[0m"""


def _confirm_action(tool_name: str, inputs: dict) -> bool:
    """Ask the user to confirm a destructive action."""
    if tool_name == "write_file":
        desc = f"write_file → {inputs.get('path', '?')} ({len(inputs.get('content', ''))} chars)"
    elif tool_name == "edit_file":
        desc = f"edit_file → {inputs.get('path', '?')}"
    elif tool_name == "bash":
        cmd = inputs.get("command", "")
        desc = f"bash → {cmd[:80]}{'...' if len(cmd) > 80 else ''}"
    else:
        desc = f"{tool_name}({inputs})"

    try:
        answer = input(f"\n  \033[33m[confirm]\033[0m {desc}\n  Allow? [Y/n]: ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return False
    return answer in ("", "y", "yes")


def _read_multiline() -> str:
    """Read multi-line input until an empty line is entered."""
    print("  \033[90m(Enter your text, finish with an empty line)\033[0m")
    lines: list[str] = []
    while True:
        try:
            line = input("  ... ")
        except (KeyboardInterrupt, EOFError):
            break
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def main() -> None:
    try:
        backend, openai_configs = resolve_backend()
    except ConfigurationError as e:
        print(f"\033[31m{e}\033[0m")
        sys.exit(1)

    system = load_system_prompt()
    messages: list = []
    tracker = TokenTracker()

    # Current model override (for /model command)
    model_override: str | None = None

    # Setup confirmation mode
    if confirm_mode():
        set_confirm_callback(_confirm_action)

    print(BANNER)
    if backend == "openai":
        n_groq = len(keys_mod.collect_api_keys("GROQ_API_KEY", "GROQ_API_KEYS"))
        n_gem = len(keys_mod.collect_api_keys("GEMINI_API_KEY", "GEMINI_API_KEYS"))
        print(f"  \033[32mBackend:\033[0m OpenAI-compatible ({len(openai_configs or [])} key slot(s); {n_groq} Groq, {n_gem} Gemini)")
    else:
        print("  \033[32mBackend:\033[0m Anthropic Claude")

    if confirm_mode():
        print("  \033[32m✓\033[0m Confirm mode enabled")

    if Path("CLAUDE.md").exists():
        print("  \033[32m✓\033[0m Loaded CLAUDE.md")

    print("  Type /help for commands. Ctrl+C or 'exit' to quit.\n")

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

        # ─── Slash commands ───────────────────────────────────────────────
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            if cmd == "/help":
                print(HELP_TEXT)
                continue

            elif cmd == "/clear":
                messages.clear()
                tracker = TokenTracker()
                print("  \033[32m✓\033[0m Conversation cleared.\n")
                continue

            elif cmd == "/save":
                name = arg or "default"
                path = save_session(name, messages)
                print(f"  \033[32m✓\033[0m Session saved to {path}\n")
                continue

            elif cmd == "/load":
                name = arg or "default"
                loaded = load_session(name)
                if loaded is None:
                    print(f"  \033[31mSession '{name}' not found.\033[0m\n")
                else:
                    messages.clear()
                    messages.extend(loaded)
                    print(f"  \033[32m✓\033[0m Loaded session '{name}' ({len(messages)} messages)\n")
                continue

            elif cmd == "/sessions":
                sessions = list_sessions()
                if sessions:
                    print("  Saved sessions:")
                    for s in sessions:
                        print(f"    - {s}")
                else:
                    print("  No saved sessions.")
                print()
                continue

            elif cmd == "/model":
                if not arg:
                    if model_override:
                        print(f"  Current model override: {model_override}")
                    else:
                        print("  No model override set. Usage: /model <name>")
                else:
                    model_override = arg
                    # Update configs if using OpenAI backend
                    if backend == "openai" and openai_configs:
                        openai_configs = [
                            (base_url, api_key, model_override)
                            for base_url, api_key, _ in openai_configs
                        ]
                    print(f"  \033[32m✓\033[0m Model set to: {model_override}\n")
                continue

            elif cmd in ("/tokens", "/cost"):
                active_model = ANTHROPIC_MODEL if backend == "anthropic" else (
                    model_override or (openai_configs[0][2] if openai_configs else "")
                )
                print(f"  \033[36m{tracker.summary(active_model)}\033[0m\n")
                continue

            elif cmd == "/paste":
                user_input = _read_multiline()
                if not user_input:
                    continue
                # Fall through to send as a message

            elif cmd == "/compact":
                if len(messages) <= 2:
                    print("  Nothing to compact.\n")
                    continue
                kept = len(messages)
                if backend == "anthropic" and anthropic_client:
                    print("  \033[90mSummarizing conversation...\033[0m", end="", flush=True)
                    try:
                        summary = compact_messages(anthropic_client, messages, system, tracker)
                        messages.clear()
                        messages.append({
                            "role": "user",
                            "content": f"<previous_context>\n{summary}\n</previous_context>\n\nLet's continue.",
                        })
                        messages.append({
                            "role": "assistant",
                            "content": "Understood — I have the context from our previous conversation. How can I help you continue?",
                        })
                        print(f"\r  \033[32m✓\033[0m Compacted {kept} messages into a summary.\n")
                    except Exception as e:
                        print(f"\n  \033[31mCompact failed: {e}\033[0m — falling back to truncation.\n")
                        while len(messages) > 4:
                            messages.pop(1)
                else:
                    while len(messages) > 4:
                        messages.pop(1)
                    print(f"  \033[32m✓\033[0m Compacted: {kept} → {len(messages)} messages\n")
                continue

            else:
                print(f"  \033[31mUnknown command: {cmd}\033[0m (type /help)\n")
                continue

        # ─── Send message ─────────────────────────────────────────────────
        messages.append({"role": "user", "content": user_input})

        label = "Assistant" if backend == "openai" else "Claude"
        print(f"\n\033[1m{label}:\033[0m ", end="", flush=True)
        try:
            if backend == "anthropic" and anthropic_client:
                response = run_agent_anthropic(
                    anthropic_client, messages, system,
                    stream=True, tracker=tracker,
                )
            else:
                response = run_agent_openai(
                    openai_configs or [], messages, system,
                    stream=True, tracker=tracker,
                )
            # If streaming, text was already printed; if not, print it
            if not response:
                pass  # streaming already printed
            elif response and not any(c in response for c in ['\x1b']):
                # Only print if streaming didn't already output (check if it's new)
                pass
        except anthropic.APIError as e:
            print(f"\n\033[31mAPI error: {e}\033[0m")
            messages.pop()
        except Exception as e:
            print(f"\n\033[31mError: {e}\033[0m")
            messages.pop()

        # Show token usage inline
        if tracker.api_calls > 0:
            active_model = ANTHROPIC_MODEL if backend == "anthropic" else (
                model_override or (openai_configs[0][2] if openai_configs else "")
            )
            print(f"\n  \033[90m{tracker.summary(active_model)}\033[0m")
        print()


if __name__ == "__main__":
    main()

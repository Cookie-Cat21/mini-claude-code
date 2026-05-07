"""Agent loop using the OpenAI SDK (Groq, Gemini OpenAI-compat, or any compatible endpoint)."""

from __future__ import annotations

import json
import random
from collections.abc import Callable

from openai import APIConnectionError, APIError, AuthenticationError, OpenAI, RateLimitError

from runtime import max_agent_rounds
from tools import execute_tool, tools_for_openai

_TOOLS = tools_for_openai()

EmitFn = Callable[[dict], None] | None


def _log_tool(name: str, inputs: dict, result: str, on_event: EmitFn) -> None:
    preview = result[:300] + ("..." if len(result) > 300 else "")
    if on_event:
        on_event({"type": "tool", "name": name, "input": inputs, "result_preview": preview})
    else:
        print(f"\n  \033[33m[tool]\033[0m {name}({inputs!r})")
        print(f"  \033[90m{preview}\033[0m")


def _assistant_message_dict(msg) -> dict:
    d: dict = {"role": "assistant", "content": msg.content}
    if msg.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments or "{}"},
            }
            for tc in msg.tool_calls
        ]
    return d


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, RateLimitError):
        return True
    if isinstance(exc, APIConnectionError):
        return True
    if isinstance(exc, AuthenticationError):
        return False
    if isinstance(exc, APIError):
        code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        if code in (408, 429, 500, 502, 503, 504):
            return True
    return False


def run_agent_openai(
    configs: list[tuple[str, str, str]],
    messages: list,
    system: str,
    max_tokens: int = 8192,
    on_event: EmitFn = None,
    max_tool_rounds: int | None = None,
) -> str:
    """
    Run tool-using agent. `configs` is a list of (base_url, api_key, model), tried in order
    with random starting offset so keys are load-balanced; on retryable errors, advance to next.
    Mutates `messages` with assistant and tool messages for session history.
    If `on_event` is set, emits dict events instead of printing tools to the terminal
    (`type`: `tool`, `assistant`; used by the HTTP SSE API).
    `max_tool_rounds` defaults to `MINI_CODE_MAX_TOOL_ROUNDS` (or 64).
    """
    if not configs:
        raise ValueError("No API configurations available (missing keys?).")

    cap = max_tool_rounds if max_tool_rounds is not None else max_agent_rounds()

    start = random.randrange(0, len(configs))
    last_error: Exception | None = None

    for offset in range(len(configs)):
        base_url, api_key, model = configs[(start + offset) % len(configs)]
        client = OpenAI(api_key=api_key, base_url=base_url)

        try:
            return _loop_until_text(client, model, messages, system, max_tokens, on_event, cap)
        except (RateLimitError, APIConnectionError, AuthenticationError, APIError) as e:
            last_error = e
            if isinstance(e, AuthenticationError):
                continue
            if _is_retryable(e):
                continue
            raise
        except Exception:
            raise

    if last_error:
        raise last_error
    raise RuntimeError("OpenAI agent loop failed without a specific error.")


def _loop_until_text(
    client: OpenAI,
    model: str,
    messages: list,
    system: str,
    max_tokens: int,
    on_event: EmitFn,
    max_tool_rounds: int,
) -> str:
    rounds = 0
    while True:
        rounds += 1
        if rounds > max_tool_rounds:
            raise RuntimeError(
                f"Exceeded maximum agent steps ({max_tool_rounds} model calls). "
                "Increase MINI_CODE_MAX_TOOL_ROUNDS if needed."
            )

        api_messages: list = []
        if system:
            api_messages.append({"role": "system", "content": system})
        api_messages.extend(messages)

        response = client.chat.completions.create(
            model=model,
            messages=api_messages,
            tools=_TOOLS,
            tool_choice="auto",
            max_tokens=max_tokens,
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            messages.append(_assistant_message_dict(msg))
            for tc in msg.tool_calls:
                name = tc.function.name
                raw_args = tc.function.arguments or "{}"
                try:
                    parsed = json.loads(raw_args)
                except json.JSONDecodeError as e:
                    result = (
                        f"Error: invalid JSON in tool arguments for {name!r}: {e}. "
                        f"Raw: {raw_args[:800]!r}"
                    )
                    inputs: dict = {}
                else:
                    if not isinstance(parsed, dict):
                        result = (
                            f"Error: tool arguments for {name!r} must be a JSON object, "
                            f"got {type(parsed).__name__}."
                        )
                        inputs = {}
                    else:
                        inputs = parsed
                        result = execute_tool(name, inputs)
                _log_tool(name, inputs, result, on_event)
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
            continue

        text = (msg.content or "").strip()
        messages.append({"role": "assistant", "content": msg.content or ""})
        if on_event:
            on_event({"type": "assistant", "content": text})
        return text

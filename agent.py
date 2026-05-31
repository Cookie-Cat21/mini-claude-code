import anthropic

from runtime import TokenTracker, max_agent_rounds, truncate_messages
from tools import TOOLS, execute_tool

MODEL = "claude-sonnet-4-6"
_CACHE_BETAS = ["prompt-caching-2024-07-31"]


def _make_system_cached(system: str) -> list[dict]:
    """Wrap system string into Anthropic's cached system block format."""
    return [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]


def _fmt_inputs(inputs: dict) -> str:
    parts = []
    for k, v in inputs.items():
        v_str = str(v).replace("\n", "\\n")
        if len(v_str) > 60:
            v_str = v_str[:57] + "..."
        parts.append(f"{k}={v_str!r}")
    return ", ".join(parts)


def _text_from_assistant_content(content: list) -> str:
    parts: list[str] = []
    for block in content:
        if getattr(block, "type", None) == "text":
            parts.append(getattr(block, "text", "") or "")
    return "".join(parts).strip()


_COMPACT_PROMPT = (
    "Summarize the entire conversation above into a concise but complete context summary. "
    "Cover: files modified (with paths), key decisions, code written, errors encountered, "
    "and current state. Write in second person (\"You were...\", \"The user asked...\"). "
    "Be thorough but brief — a future agent reading this should be able to continue seamlessly."
)


def compact_messages(
    client: anthropic.Anthropic,
    messages: list,
    system: str = "",
    tracker: TokenTracker | None = None,
) -> str:
    """Summarize a conversation into a compact context string via LLM call."""
    payload = list(messages) + [{"role": "user", "content": _COMPACT_PROMPT}]
    kwargs: dict = dict(model=MODEL, max_tokens=2048, messages=payload)
    if system:
        kwargs["system"] = _make_system_cached(system)
        kwargs["betas"] = _CACHE_BETAS

    response = client.messages.create(**kwargs)
    if tracker and hasattr(response, "usage") and response.usage:
        tracker.add(
            getattr(response.usage, "input_tokens", 0) or 0,
            getattr(response.usage, "output_tokens", 0) or 0,
            getattr(response.usage, "cache_read_input_tokens", 0) or 0,
            getattr(response.usage, "cache_creation_input_tokens", 0) or 0,
        )
    return _text_from_assistant_content(response.content)


def run_agent_anthropic(
    client: anthropic.Anthropic,
    messages: list,
    system: str = "",
    max_tool_rounds: int | None = None,
    stream: bool = False,
    tracker: TokenTracker | None = None,
) -> str:
    """Agentic loop: keep calling Claude and executing tools until end_turn."""
    cap = max_tool_rounds if max_tool_rounds is not None else max_agent_rounds()
    rounds = 0
    while True:
        rounds += 1
        if rounds > cap:
            raise RuntimeError(
                f"Exceeded maximum agent steps ({cap} model calls). "
                "Increase MINI_CODE_MAX_TOOL_ROUNDS if needed."
            )

        # Context window management
        truncate_messages(messages, MODEL)

        kwargs: dict = dict(model=MODEL, max_tokens=8096, tools=TOOLS, messages=messages)
        if system:
            kwargs["system"] = _make_system_cached(system)
            kwargs["betas"] = _CACHE_BETAS

        if stream:
            return _stream_anthropic(client, kwargs, messages, system, cap, rounds, tracker)

        response = client.messages.create(**kwargs)

        if tracker and hasattr(response, "usage") and response.usage:
            tracker.add(
                getattr(response.usage, "input_tokens", 0) or 0,
                getattr(response.usage, "output_tokens", 0) or 0,
                getattr(response.usage, "cache_read_input_tokens", 0) or 0,
                getattr(response.usage, "cache_creation_input_tokens", 0) or 0,
            )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            return _text_from_assistant_content(response.content)

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\n  \033[33m[tool]\033[0m {block.name}({_fmt_inputs(block.input)})")
                result = execute_tool(block.name, block.input)
                preview = result[:300] + ("..." if len(result) > 300 else "")
                print(f"  \033[90m{preview}\033[0m")
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": result}
                )

        if tool_results:
            messages.append({"role": "user", "content": tool_results})
            continue

        partial = _text_from_assistant_content(response.content)
        if partial:
            return partial
        return ""


def _stream_anthropic(
    client: anthropic.Anthropic,
    kwargs: dict,
    messages: list,
    system: str,
    cap: int,
    rounds: int,
    tracker: TokenTracker | None,
) -> str:
    """Stream Anthropic response, printing tokens as they arrive."""
    collected_text = ""
    collected_content_blocks: list = []
    current_tool_input = ""
    current_tool_name = ""
    current_tool_id = ""
    in_tool = False

    with client.messages.stream(**kwargs) as stream:
        for event in stream:
            if event.type == "content_block_start":
                block = event.content_block
                if hasattr(block, "type") and block.type == "tool_use":
                    in_tool = True
                    current_tool_name = block.name
                    current_tool_id = block.id
                    current_tool_input = ""
                elif hasattr(block, "type") and block.type == "text":
                    in_tool = False

            elif event.type == "content_block_delta":
                delta = event.delta
                if hasattr(delta, "type"):
                    if delta.type == "text_delta":
                        text = delta.text
                        print(text, end="", flush=True)
                        collected_text += text
                    elif delta.type == "input_json_delta":
                        current_tool_input += delta.partial_json

            elif event.type == "content_block_stop":
                if in_tool:
                    collected_content_blocks.append({
                        "type": "tool_use",
                        "id": current_tool_id,
                        "name": current_tool_name,
                        "input_json": current_tool_input,
                    })
                    in_tool = False

            elif event.type == "message_delta":
                pass

    # Get final message for usage tracking
    final_message = stream.get_final_message()
    if tracker and final_message and hasattr(final_message, "usage") and final_message.usage:
        tracker.add(
            getattr(final_message.usage, "input_tokens", 0) or 0,
            getattr(final_message.usage, "output_tokens", 0) or 0,
            getattr(final_message.usage, "cache_read_input_tokens", 0) or 0,
            getattr(final_message.usage, "cache_creation_input_tokens", 0) or 0,
        )

    # If there were tool uses, execute them
    if collected_content_blocks:
        # Build the assistant content as the API expects
        messages.append({"role": "assistant", "content": final_message.content})

        tool_results = []
        for block_data in collected_content_blocks:
            name = block_data["name"]
            try:
                import json
                inputs = json.loads(block_data["input_json"]) if block_data["input_json"] else {}
            except Exception:
                inputs = {}
            print(f"\n  \033[33m[tool]\033[0m {name}({_fmt_inputs(inputs)})")
            result = execute_tool(name, inputs)
            preview = result[:300] + ("..." if len(result) > 300 else "")
            print(f"  \033[90m{preview}\033[0m")
            tool_results.append(
                {"type": "tool_result", "tool_use_id": block_data["id"], "content": result}
            )

        messages.append({"role": "user", "content": tool_results})

        # Continue the loop
        if rounds < cap:
            truncate_messages(messages, MODEL)
            new_kwargs: dict = dict(model=MODEL, max_tokens=8096, tools=TOOLS, messages=messages)
            if system:
                new_kwargs["system"] = _make_system_cached(system)
                new_kwargs["betas"] = _CACHE_BETAS
            return _stream_anthropic(client, new_kwargs, messages, system, cap, rounds + 1, tracker)
        else:
            raise RuntimeError(
                f"Exceeded maximum agent steps ({cap} model calls). "
                "Increase MINI_CODE_MAX_TOOL_ROUNDS if needed."
            )

    # Final text
    messages.append({"role": "assistant", "content": final_message.content})
    return collected_text

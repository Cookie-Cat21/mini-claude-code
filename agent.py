import anthropic

from runtime import max_agent_rounds
from tools import TOOLS, execute_tool

MODEL = "claude-sonnet-4-6"


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


def run_agent_anthropic(
    client: anthropic.Anthropic,
    messages: list,
    system: str = "",
    max_tool_rounds: int | None = None,
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

        kwargs = dict(model=MODEL, max_tokens=8096, tools=TOOLS, messages=messages)
        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)
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

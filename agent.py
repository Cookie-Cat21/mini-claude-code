import anthropic
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


def run_agent_anthropic(client: anthropic.Anthropic, messages: list, system: str = "") -> str:
    """Agentic loop: keep calling Claude and executing tools until end_turn."""
    while True:
        kwargs = dict(model=MODEL, max_tokens=8096, tools=TOOLS, messages=messages)
        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        # Execute all tool calls in this turn
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

        messages.append({"role": "user", "content": tool_results})

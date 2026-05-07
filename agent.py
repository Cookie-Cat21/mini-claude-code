import json
import groq
from tools import TOOLS, execute_tool

MODEL = "llama-3.3-70b-versatile"


def _fmt_inputs(inputs: dict) -> str:
    parts = []
    for k, v in inputs.items():
        v_str = str(v).replace("\n", "\\n")
        if len(v_str) > 60:
            v_str = v_str[:57] + "..."
        parts.append(f"{k}={v_str!r}")
    return ", ".join(parts)


def run_agent(client: groq.Groq, messages: list, system: str = "") -> str:
    """Agentic loop: keep calling the model and executing tools until stop."""
    while True:
        all_messages = []
        if system:
            all_messages = [{"role": "system", "content": system}] + messages
        else:
            all_messages = list(messages)

        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=8096,
            tools=TOOLS,
            messages=all_messages,
        )

        choice = response.choices[0]
        message = choice.message
        finish_reason = choice.finish_reason

        # Persist the assistant turn (tool_calls may be None)
        assistant_entry = {"role": "assistant", "content": message.content}
        if message.tool_calls:
            assistant_entry["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in message.tool_calls
            ]
        messages.append(assistant_entry)

        if finish_reason == "stop" or not message.tool_calls:
            return message.content or ""

        # Execute all tool calls and append results
        for tc in message.tool_calls:
            name = tc.function.name
            try:
                inputs = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                inputs = {}
            print(f"\n  \033[33m[tool]\033[0m {name}({_fmt_inputs(inputs)})")
            result = execute_tool(name, inputs)
            preview = result[:300] + ("..." if len(result) > 300 else "")
            print(f"  \033[90m{preview}\033[0m")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

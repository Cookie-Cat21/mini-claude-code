import json
import subprocess
import glob as glob_module
from pathlib import Path

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file, creating it or overwriting if it exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to write"},
                    "content": {"type": "string", "description": "Content to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a bash/shell command and return stdout and stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files matching a glob pattern (e.g. '**/*.py').",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern"}
                },
                "required": ["pattern"],
            },
        },
    },
]


def execute_tool(name: str, inputs: dict) -> str:
    if name == "read_file":
        try:
            return Path(inputs["path"]).read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {e}"

    elif name == "write_file":
        try:
            path = Path(inputs["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(inputs["content"], encoding="utf-8")
            return f"Wrote {len(inputs['content'])} chars to {path}"
        except Exception as e:
            return f"Error writing file: {e}"

    elif name == "bash":
        try:
            result = subprocess.run(
                inputs["command"],
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
            )
            output = result.stdout
            if result.stderr:
                output += result.stderr
            return output.strip() or f"(exit code {result.returncode})"
        except subprocess.TimeoutExpired:
            return "Error: command timed out after 60s"
        except Exception as e:
            return f"Error running command: {e}"

    elif name == "list_files":
        matches = glob_module.glob(inputs["pattern"], recursive=True)
        return "\n".join(sorted(matches)) if matches else "No files found."

    return f"Unknown tool: {name}"

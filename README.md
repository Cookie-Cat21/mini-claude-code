# mini-claude-code

A minimal AI coding assistant CLI built on the Claude API — your own pocket-sized Claude Code in ~150 lines of Python.

## What it does

- Reads and writes files in your project
- Runs shell commands
- Searches files with glob patterns
- Keeps full conversation history within a session
- Loads `CLAUDE.md` for project-specific context

## How it works

```
You: fix the bug in app.py

Claude:
  [tool] read_file(path='app.py')
  <reads the file>
  [tool] write_file(path='app.py', content='...')
  <applies the fix>

  Done — fixed the off-by-one error on line 42.
```

Claude decides which tools to call, executes them, and loops until the task is complete. That's the agentic loop.

## Setup

```bash
git clone https://github.com/Cookie-Cat21/mini-claude-code
cd mini-claude-code
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
python main.py
```

## Project structure

| File | What it does |
|------|-------------|
| `main.py` | CLI entry point, REPL loop |
| `agent.py` | Agentic loop — calls Claude, executes tools, repeats |
| `tools.py` | Tool definitions + implementations (`read_file`, `write_file`, `bash`, `list_files`) |

## Adding your own tools

1. Add a tool definition to `TOOLS` in `tools.py`
2. Add the matching `elif name == "your_tool"` branch in `execute_tool`

That's it — Claude will automatically use the new tool when relevant.

## CLAUDE.md support

Drop a `CLAUDE.md` in any directory before running. Its contents get injected into the system prompt as project context — same as the real Claude Code.

# mini-claude-code

A minimal AI coding assistant CLI: **Groq**, **Gemini** (OpenAI-compatible endpoint), or **Anthropic Claude**, with the same tools (`read_file`, `write_file`, `bash`, `list_files`).

## What it does

- Reads and writes files in your project
- Runs shell commands
- Lists files with glob patterns
- Keeps full conversation history within a session
- Loads `CLAUDE.md` for project-specific context
- **Multiple API keys**: set `GROQ_API_KEYS` or `GEMINI_API_KEYS` (comma-separated); the client rotates and fails over on rate limits

## Setup

```bash
pip install -r requirements.txt
```

### Provider selection (`MINI_CODE_PROVIDER`)

| Value | Behavior |
|--------|----------|
| `auto` (default) | Use Groq + Gemini keys if any are set (Groq first, then Gemini). Otherwise use `ANTHROPIC_API_KEY`. |
| `groq` | Only Groq (`GROQ_API_KEY` / `GROQ_API_KEYS`) |
| `gemini` | Only Gemini (`GEMINI_API_KEY` / `GEMINI_API_KEYS`) |
| `anthropic` | Only Claude (`ANTHROPIC_API_KEY`) |

### Environment variables

```bash
# Groq (OpenAI-compatible)
export GROQ_API_KEY=...
# or several keys (comma or newline separated):
export GROQ_API_KEYS=key1,key2,key3
export GROQ_MODEL=llama-3.3-70b-versatile   # optional

# Gemini (OpenAI-compatible API)
export GEMINI_API_KEY=...
export GEMINI_API_KEYS=k1,k2
export GEMINI_MODEL=gemini-2.0-flash        # optional

# Claude (when using anthropic or auto with no Groq/Gemini keys)
export ANTHROPIC_API_KEY=...

python3 main.py
```

## Testing

```bash
pip install -r requirements.txt
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## Project structure

| File | Role |
|------|------|
| `main.py` | CLI, provider routing |
| `agent.py` | Anthropic agent loop |
| `agent_openai.py` | Groq / Gemini loop (OpenAI SDK) |
| `tools.py` | Tool definitions + execution |
| `keys.py` | Parse single or multi API keys from env |

## Adding tools

1. Add a definition to `TOOLS` in `tools.py`
2. Add a branch in `execute_tool`

OpenAI-format tools are derived automatically from the same schema.

## CLAUDE.md

Drop a `CLAUDE.md` in the working directory before running. Its contents are appended to the system prompt.

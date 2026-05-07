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

# Cap how many model round-trips one request may take (each completion = one round; tool loops count).
# Default 64, clamped between 1 and 10000. Applies to CLI and HTTP Groq/Gemini agent runs.
export MINI_CODE_MAX_TOOL_ROUNDS=64   # optional

python3 main.py
```

## HTTP API (Fly.io, Railway, VPS, …)

Stateless JSON and **SSE** endpoints for the Groq/Gemini path (same OpenAI-style `messages` array as the CLI). **Anthropic** is not exposed over SSE; use `python3 main.py` for Claude.

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness |
| `GET /meta` | Whether `POST /chat/stream` is available for current env |
| `POST /chat` | JSON body `{"messages":[...], "system": null}` → `{"text","messages"}` |
| `POST /chat/stream` | **Server-Sent Events**: `data: {"type":"tool"|"assistant"|"error"|"done",...}` |

**Environment (server)**

- Same provider keys as the CLI (`GROQ_*`, `GEMINI_*`, `MINI_CODE_PROVIDER`).
- `MINI_CODE_MAX_TOOL_ROUNDS` — same as CLI; limits model calls per `/chat` or `/chat/stream` request (default `64`).
- `CHAT_API_SECRET` — if set, require `Authorization: Bearer <secret>` or `X-Api-Key` on `POST /chat` and `POST /chat/stream`. **`GET /health` and `GET /meta` stay public** (no secret).
- `CORS_ORIGINS` — comma-separated list for browser calls (e.g. `https://your-app.vercel.app`). Default `*` (credentials disabled). For credentials, list explicit origins.

**Run locally**

```bash
pip install -r requirements.txt
export GROQ_API_KEY=...
uvicorn fly_server:app --host 0.0.0.0 --port 8080
```

**Docker / Fly**

```bash
docker build -t mini-claude-code .
docker run -e GROQ_API_KEY=... -e CHAT_API_SECRET=... -p 8080:8080 mini-claude-code
```

Use `fly.toml` + `Dockerfile` in this repo: `fly launch` then `fly secrets set GROQ_API_KEY=...` (and optional `CHAT_API_SECRET`, `CORS_ORIGINS`).

## Vercel (static UI)

The `web/` folder is a **static** chat shell that calls your Fly API URL from the browser.

1. Create a Vercel project and set **Root Directory** to `web` (or deploy only that folder).
2. Open the deployed page, enter your Fly `https://…fly.dev` base URL (and optional bearer secret if you set `CHAT_API_SECRET` on Fly).

Keys stay on Fly; the browser never sees `GROQ_API_KEY`.

**Repo-root Vercel:** **`vercel.json`** installs **`requirements.txt`** + **`demo-glass`** (`npm ci`), **`vite build`**, copies **`demo-glass/dist`** → **`public/`** (glass **`/`**). **`api/index.py`** is **JSON-only** (`POST /api/chat`, `GET /health`) — it must not serve HTML or catch-all **`GET`s**, or **`/assets/*.js`** breaks. **`POST /api/chat`** rewrites to the Python function. **`pyproject.toml`** → **`[tool.vercel] entrypoint = "api.index:app"`**. Set **`GROQ_API_KEY`**. **`MiniCodeChat`** uses same-origin **`/api/chat`**. Dashboard preview **403** is often **Deployment Protection** on thumbnails.

## Proof ledger (Databricks / Delta)

Optional **append-only audit trail** for assistant answers: store natural-language replies next to **evidence pointers** (Unity Catalog table names, Delta versions, job ids, query ids) in a Delta table so narratives stay tied to warehouse facts.

- Python helpers live in `ledger/` (`ProofLedgerRecord`, `EvidencePointer`, `append_proof_records`).
- Extra deps (not required for the CLI/server): `pip install -r requirements-ledger.txt` (`deltalake`, `pyarrow`).
- Example script: `examples/proof_ledger_append.py` posts to your deployed `POST /api/chat`, then appends one ledger row (pass `--chat-url` or `VERCEL_CHAT_URL`).
- Typical pattern in Databricks: notebook/job reads curated metrics → builds `EvidencePointer` rows → calls your Vercel URL → appends with `append_proof_records("dbfs:/...", [...])` using cluster credentials.

## Project structure

| File | Role |
|------|------|
| `main.py` | CLI, provider routing |
| `runtime.py` | Shared env resolution + system prompt |
| `demo-glass/` | Glass Vite UI — built by root `vercel.json`; chat → `/api/chat` |
| `api/index.py` | Vercel Groq API (`POST /api/chat`); glass UI from `public/` |
| `fly_server.py` | FastAPI HTTP + SSE (Fly / Docker) |
| `agent.py` | Anthropic agent loop |
| `agent_openai.py` | Groq / Gemini loop (OpenAI SDK) |
| `tools.py` | Tool definitions + execution |
| `keys.py` | Parse single or multi API keys from env |
| `ledger/` | Optional Delta “proof ledger” (audit rows + evidence JSON) |
| `examples/proof_ledger_append.py` | Example: Vercel chat → append ledger row |
| `tests/` | Unit tests (`python3 -m unittest discover …`) |
| `Dockerfile` | Container image for Fly / Docker |
| `fly.toml` | Fly Machines scaffold |
| `web/index.html` | Minimal static UI for Vercel |
| `vercel.json` | Root deploy: Vite → `public/`, rewrite `POST /api/chat` → Python |

## Adding tools

1. Add a definition to `TOOLS` in `tools.py`
2. Add a branch in `execute_tool`

OpenAI-format tools are derived automatically from the same schema.

## Testing

```bash
pip install -r requirements.txt
pip install -r requirements-ledger.txt   # optional; enables Delta ledger tests
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

## CLAUDE.md

Drop a `CLAUDE.md` in the working directory before running. Its contents are appended to the system prompt.

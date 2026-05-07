"""HTTP + SSE API for the coding agent (intended for Fly.io or similar).

Requires Groq and/or Gemini keys (OpenAI-compatible flow). Claude-only setups
return 503 on /chat/stream — use the CLI for Anthropic.
"""

from __future__ import annotations

import asyncio
import copy
import json
import os
import queue
import threading

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agent_openai import run_agent_openai
from runtime import ConfigurationError, load_system_prompt, resolve_backend

app = FastAPI(title="mini-claude-code API", version="0.2.0")

_origins = os.environ.get("CORS_ORIGINS", "*").strip()
_cors_list = [o.strip() for o in _origins.split(",") if o.strip()] or ["*"]
# Browsers disallow credentials with wildcard origins.
_allow_credentials = "*" not in _cors_list
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_list,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _check_api_secret(request: Request) -> None:
    secret = os.environ.get("CHAT_API_SECRET", "").strip()
    if not secret:
        return
    auth = request.headers.get("authorization", "")
    token = auth.removeprefix("Bearer ").strip() if auth else ""
    if token == secret:
        return
    if request.headers.get("x-api-key", "").strip() == secret:
        return
    raise HTTPException(status_code=401, detail="Invalid or missing API secret.")


class ChatRequest(BaseModel):
    messages: list[dict] = Field(..., description="OpenAI-style chat messages (user/assistant/tool).")
    system: str | None = Field(None, description="Override system prompt; default loads CLAUDE.md if present.")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/meta")
def meta() -> dict:
    """Describe whether streaming chat is available (public; no secrets)."""
    try:
        backend, _ = resolve_backend()
    except ConfigurationError as e:
        return {"chat_stream": False, "backend": None, "error": str(e)}
    return {
        "chat_stream": backend == "openai",
        "backend": backend,
        "error": None if backend == "openai" else "Use CLI for Anthropic; HTTP stream needs Groq/Gemini.",
    }


@app.post("/chat/stream")
async def chat_stream(body: ChatRequest, request: Request) -> StreamingResponse:
    _check_api_secret(request)
    try:
        backend, openai_configs = resolve_backend()
    except ConfigurationError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    if backend != "openai" or not openai_configs:
        raise HTTPException(
            status_code=503,
            detail="Streaming HTTP API requires Groq or Gemini (OpenAI-compatible). "
            "Set GROQ_API_KEY / GEMINI_API_KEY (or *_API_KEYS). Use python main.py for Claude.",
        )

    messages = copy.deepcopy(body.messages)
    system = body.system if body.system is not None else load_system_prompt()
    q: queue.Queue = queue.Queue()

    def on_event(ev: dict) -> None:
        q.put(ev)

    def worker() -> None:
        try:
            text = run_agent_openai(openai_configs, messages, system, on_event=on_event)
            q.put({"type": "done", "text": text, "messages": messages})
        except Exception as e:
            q.put({"type": "error", "message": str(e)})
        finally:
            q.put(None)

    threading.Thread(target=worker, daemon=True).start()

    async def event_gen():
        while True:
            item = await asyncio.to_thread(q.get)
            if item is None:
                break
            yield f"data: {json.dumps(item, default=str)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.post("/chat", response_model=None)
def chat_sync(body: ChatRequest, request: Request) -> dict:
    """Non-streaming JSON response (simpler for clients that do not parse SSE)."""
    _check_api_secret(request)
    try:
        backend, openai_configs = resolve_backend()
    except ConfigurationError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    if backend != "openai" or not openai_configs:
        raise HTTPException(
            status_code=503,
            detail="This endpoint requires Groq or Gemini. "
            "Set GROQ_API_KEY / GEMINI_API_KEY (or *_API_KEYS). Use python main.py for Claude.",
        )

    messages = copy.deepcopy(body.messages)
    system = body.system if body.system is not None else load_system_prompt()

    try:
        text = run_agent_openai(openai_configs, messages, system)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return {"text": text, "messages": messages}

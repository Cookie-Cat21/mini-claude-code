"""Vercel Groq JSON API only.

The glass SPA is served from repo-root ``public/`` (built from ``demo-glass/``).
This module must not serve HTML on ``GET /`` or catch-all paths — doing so breaks
``/assets/*.js`` (wrong MIME) and hides the React UI.
"""

from __future__ import annotations

import os
from typing import List

import groq
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

app = FastAPI(
    title="mini-claude-code",
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
)


class VercelPostPathMiddleware(BaseHTTPMiddleware):
    """Map POST ``/api/index`` (function URL) → ``POST /api/chat``."""

    PREFIX = "/api/index"

    async def dispatch(self, request: Request, call_next):
        path = request.scope.get("path") or ""
        method = request.method.upper()
        if method == "POST" and path in (self.PREFIX, self.PREFIX + "/"):
            request.scope["path"] = "/api/chat"
            request.scope["raw_path"] = b"/api/chat"
        return await call_next(request)


app.add_middleware(VercelPostPathMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

MODEL = "llama-3.3-70b-versatile"
SYSTEM_PROMPT = (
    "You are an expert software engineer and coding assistant. "
    "Help users with coding questions, explain concepts, review code, debug issues, "
    "and provide technical guidance. Be concise and direct. "
    "Use markdown code blocks with language tags for all code."
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    new_message: str


@app.get("/health")
async def health():
    """Tiny probe for deploy smoke checks (optional)."""

    return {"status": "ok"}


@app.post("/api/chat")
async def chat(req: ChatRequest):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY environment variable is not set")

    client = groq.Groq(api_key=api_key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [{"role": m.role, "content": m.content} for m in req.messages]
    messages.append({"role": "user", "content": req.new_message})

    response = client.chat.completions.create(
        model=MODEL,
        max_tokens=4096,
        messages=messages,
    )

    reply = response.choices[0].message.content or ""
    updated = [{"role": m.role, "content": m.content} for m in req.messages]
    updated.append({"role": "user", "content": req.new_message})
    updated.append({"role": "assistant", "content": reply})
    return {"response": reply, "messages": updated}

"""mini-claude-code web: FastAPI wrapper for Vercel deployment."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import groq
import os
from typing import List

app = FastAPI(title="mini-claude-code")

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


@app.get("/")
async def root():
    return RedirectResponse(url="https://mini-claude-glass.vercel.app", status_code=302)


@app.get("/health")
async def health():
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

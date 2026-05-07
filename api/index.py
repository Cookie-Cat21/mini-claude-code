"""mini-claude-code web: FastAPI wrapper for Vercel deployment."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import groq
import os
from typing import List

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

app = FastAPI(title="mini-claude-code")


class VercelRewritePathMiddleware(BaseHTTPMiddleware):
    """Vercel rewrites ``/(.*)`` → ``/api/index``; ASGI scope path is often ``/api/index``, not ``/``."""

    PREFIX = "/api/index"

    async def dispatch(self, request: Request, call_next):
        path = request.scope.get("path") or ""
        if path == self.PREFIX or path.startswith(self.PREFIX + "/"):
            suffix = path[len(self.PREFIX) :] or "/"
            request.scope["path"] = suffix if suffix.startswith("/") else "/" + suffix
            request.scope["raw_path"] = request.scope["path"].encode("utf-8")
        return await call_next(request)


app.add_middleware(VercelRewritePathMiddleware)
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

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>mini-claude-code</title>
  <script src="https://cdn.jsdelivr.net/npm/marked@9/marked.min.js"></script>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:#0d1117;color:#e6edf3;font-family:'Courier New',monospace;height:100vh;display:flex;flex-direction:column}
    header{border-bottom:1px solid #21262d;padding:14px 24px;display:flex;align-items:center;gap:16px}
    .logo{color:#58a6ff;font-size:1.1rem;font-weight:700}
    .tagline{color:#8b949e;font-size:.8rem;margin-top:2px}
    #chat{flex:1;overflow-y:auto;padding:20px 24px;display:flex;flex-direction:column;gap:14px}
    .welcome{text-align:center;padding:60px 20px;color:#8b949e}
    .welcome h2{color:#58a6ff;margin-bottom:8px;font-size:1.3rem}
    .welcome p{font-size:.9rem;line-height:1.6}
    .welcome ul{list-style:none;margin-top:12px;font-size:.85rem}
    .welcome ul li::before{content:"› ";color:#58a6ff}
    .message{max-width:82%;border-radius:8px;padding:12px 16px;line-height:1.65;font-size:.92rem}
    .message.user{align-self:flex-end;background:#1f6feb;color:#fff}
    .message.assistant{align-self:flex-start;background:#161b22;border:1px solid #21262d}
    .msg-label{font-size:.7rem;margin-bottom:5px;opacity:.75}
    .message.user .msg-label{color:#cce5ff}
    .message.assistant .msg-label{color:#58a6ff}
    .message.assistant p{margin:.4em 0}
    .message.assistant pre{background:#0d1117;border:1px solid #30363d;border-radius:6px;padding:12px;overflow-x:auto;margin:8px 0}
    .message.assistant code{font-family:'Courier New',monospace;font-size:.88em}
    .message.assistant p code{background:#21262d;padding:1px 5px;border-radius:4px}
    .message.assistant ul,.message.assistant ol{padding-left:1.4em;margin:.4em 0}
    .message.assistant h1,.message.assistant h2,.message.assistant h3{margin:.6em 0 .3em;color:#58a6ff}
    .thinking{color:#8b949e;font-style:italic}
    .error-msg{background:#3d1c1c;border:1px solid #f85149;border-radius:8px;color:#f85149;padding:12px 16px;align-self:stretch;font-size:.88rem}
    #input-area{border-top:1px solid #21262d;padding:14px 24px;display:flex;gap:10px;align-items:flex-end}
    #user-input{flex:1;background:#161b22;border:1px solid #21262d;border-radius:8px;color:#e6edf3;font-family:'Courier New',monospace;font-size:.92rem;padding:10px 14px;resize:none;min-height:44px;max-height:180px;outline:none;transition:border .15s}
    #user-input:focus{border-color:#388bfd}
    #user-input::placeholder{color:#484f58}
    #send-btn{background:#1f6feb;border:none;border-radius:8px;color:#fff;cursor:pointer;font-family:'Courier New',monospace;font-size:.88rem;padding:10px 18px;transition:background .2s;white-space:nowrap;height:44px}
    #send-btn:hover{background:#388bfd}
    #send-btn:disabled{background:#21262d;color:#484f58;cursor:not-allowed}
    ::-webkit-scrollbar{width:6px}
    ::-webkit-scrollbar-track{background:#0d1117}
    ::-webkit-scrollbar-thumb{background:#30363d;border-radius:3px}
  </style>
</head>
<body>
  <header>
    <div>
      <div class="logo">⌨ mini-claude-code</div>
      <div class="tagline">AI coding assistant · powered by Groq</div>
    </div>
  </header>

  <div id="chat">
    <div class="welcome">
      <h2>mini-claude-code</h2>
      <p>Your pocket-sized AI coding assistant. Ask anything about code.</p>
      <ul>
        <li>Debug and fix errors</li>
        <li>Explain concepts and code</li>
        <li>Review and refactor</li>
        <li>Answer technical questions</li>
      </ul>
    </div>
  </div>

  <div id="input-area">
    <textarea id="user-input" placeholder="Ask about code... (Enter to send, Shift+Enter for newline)" rows="1"></textarea>
    <button id="send-btn" onclick="sendMessage()">Send →</button>
  </div>

  <script>
    marked.setOptions({ breaks: true, gfm: true });

    let messages = [];
    const chat = document.getElementById('chat');
    const input = document.getElementById('user-input');
    const btn = document.getElementById('send-btn');

    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 180) + 'px';
    });

    input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });

    function appendMessage(role, content, isThinking = false) {
      document.querySelector('.welcome')?.remove();
      const div = document.createElement('div');
      div.className = 'message ' + role;
      const label = document.createElement('div');
      label.className = 'msg-label';
      label.textContent = role === 'user' ? 'You' : 'Assistant';
      div.appendChild(label);
      const body = document.createElement('div');
      if (isThinking) {
        body.className = 'thinking';
        body.textContent = content;
      } else if (role === 'assistant') {
        body.innerHTML = marked.parse(content);
      } else {
        body.textContent = content;
      }
      div.appendChild(body);
      chat.appendChild(div);
      chat.scrollTop = chat.scrollHeight;
      return div;
    }

    function appendError(msg) {
      const div = document.createElement('div');
      div.className = 'error-msg';
      div.textContent = '⚠ ' + msg;
      chat.appendChild(div);
      chat.scrollTop = chat.scrollHeight;
    }

    async function sendMessage() {
      const text = input.value.trim();
      if (!text || btn.disabled) return;
      input.value = '';
      input.style.height = 'auto';
      btn.disabled = true;
      appendMessage('user', text);
      const thinking = appendMessage('assistant', 'Thinking…', true);
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages, new_message: text })
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'HTTP ' + res.status);
        }
        const data = await res.json();
        messages = data.messages;
        thinking.remove();
        appendMessage('assistant', data.response);
      } catch (err) {
        thinking.remove();
        appendError(err.message || 'Something went wrong. Is GROQ_API_KEY set?');
      }
      btn.disabled = false;
      input.focus();
    }
  </script>
</body>
</html>"""


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    new_message: str


@app.get("/")
@app.get("/api/index")
async def root():
    return HTMLResponse(_HTML)


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
    # Return only the non-system history to the client
    updated = [{"role": m.role, "content": m.content} for m in req.messages]
    updated.append({"role": "user", "content": req.new_message})
    updated.append({"role": "assistant", "content": reply})
    return {"response": reply, "messages": updated}

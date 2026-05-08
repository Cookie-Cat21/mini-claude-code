import { useCallback, useMemo, useRef, useState } from 'react'
import { GlassSurface } from './GlassSurface'
import {
  ClaudeChatInput,
} from './ClaudeChatInput'
import { formatFileSize, type ChatSendPayload } from './chatComposerTypes'

type ChatMsg = { role: 'user' | 'assistant'; content: string }

function apiBase(): string {
  const raw = import.meta.env.VITE_CHAT_API_BASE as string | undefined
  if (raw && raw.trim()) return raw.replace(/\/$/, '')
  return ''
}

async function buildNewMessage(payload: ChatSendPayload): Promise<string | null> {
  const parts: string[] = []

  if (payload.isThinkingEnabled) {
    parts.push('Think through this step-by-step before you answer.')
  }

  for (const p of payload.pastedContent) {
    parts.push(`[Pasted content]\n${p.content}`)
  }

  for (const af of payload.files) {
    const { file } = af
    const name = file.name
    const size = formatFileSize(file.size)
    const textish =
      file.type.startsWith('text/') ||
      /\.(txt|md|json|ts|tsx|js|jsx|mjs|cjs|py|css|html|yml|yaml|csv|rs|go|java|kt)$/i.test(
        name
      )

    if (textish) {
      try {
        let t = await file.text()
        if (t.length > 48_000) t = `${t.slice(0, 48_000)}\n…[truncated]`
        parts.push(`[File: ${name} (${size})]\n${t}`)
      } catch {
        parts.push(`[Attached file: ${name} (${size})]`)
      }
    } else if (file.type.startsWith('image/')) {
      parts.push(
        `[Attached image: ${name} (${size}). Describe in text what you want inferred from it — the chat API sends text only.]`
      )
    } else {
      parts.push(`[Attached file: ${name} (${size})]`)
    }
  }

  const userLine = payload.message.trim()
  if (userLine) parts.push(userLine)

  const out = parts.join('\n\n').trim()
  return out.length > 0 ? out : null
}

export function MiniCodeChat() {
  const base = useMemo(() => apiBase(), [])
  const chatUrl = base ? `${base}/api/chat` : '/api/chat'
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const sendingRef = useRef(false)

  const onSendMessage = useCallback(
    async (payload: ChatSendPayload) => {
      if (sendingRef.current) return
      sendingRef.current = true
      setPending(true)
      setError(null)
      try {
        const text = await buildNewMessage(payload)
        if (!text) return

        const res = await fetch(chatUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages, new_message: text }),
        })
        const data = (await res.json().catch(() => ({}))) as {
          detail?: string
          response?: string
          messages?: ChatMsg[]
        }
        if (!res.ok) {
          throw new Error(data.detail ?? `HTTP ${res.status}`)
        }
        if (Array.isArray(data.messages)) {
          setMessages(data.messages)
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Request failed')
      } finally {
        sendingRef.current = false
        setPending(false)
      }
    },
    [chatUrl, messages]
  )

  return (
    <section
      id="chat"
      className="flex w-full max-w-2xl min-h-0 flex-1 flex-col justify-center gap-5"
      aria-label="Chat"
    >
      <GlassSurface className="flex max-h-[min(42dvh,22rem)] min-h-[12rem] flex-col overflow-hidden p-4 md:p-5">
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto custom-scrollbar text-sm">
          {messages.length === 0 ? (
            <p className="py-8 text-center text-white/40">
              Ask anything about code…
            </p>
          ) : (
            messages.map((m, i) => (
              <div
                key={`${i}-${m.role}`}
                className={
                  m.role === 'user'
                    ? 'ml-6 rounded-xl bg-white/12 px-3 py-2.5 text-white/95'
                    : 'mr-6 rounded-xl bg-white/6 px-3 py-2.5 text-white/88'
                }
              >
                <span className="mb-1 block text-[10px] uppercase tracking-wider text-white/38">
                  {m.role}
                </span>
                <div className="whitespace-pre-wrap">{m.content}</div>
              </div>
            ))
          )}
          {pending ? (
            <p className="text-sm text-white/45 italic">Thinking…</p>
          ) : null}
          {error ? (
            <p className="text-sm text-red-300/95">{error}</p>
          ) : null}
        </div>
      </GlassSurface>

      <ClaudeChatInput disabled={pending} onSendMessage={onSendMessage} />
    </section>
  )
}

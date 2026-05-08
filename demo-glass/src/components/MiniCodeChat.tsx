import { LobeHub } from '@lobehub/icons'
import { useCallback, useMemo, useState } from 'react'
import { GlassSurface } from './GlassSurface'

type ChatMsg = { role: 'user' | 'assistant'; content: string }

/** Same-origin `/api/chat` on unified Vercel; optional absolute API host for split deploys. */
function apiBase(): string {
  const raw = import.meta.env.VITE_CHAT_API_BASE as string | undefined
  if (raw && raw.trim()) return raw.replace(/\/$/, '')
  return ''
}

export function MiniCodeChat() {
  const base = useMemo(() => apiBase(), [])
  const chatUrl = base ? `${base}/api/chat` : '/api/chat'
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [input, setInput] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const send = useCallback(async () => {
    const text = input.trim()
    if (!text || pending) return
    setError(null)
    setPending(true)
    setInput('')
    try {
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
      setPending(false)
    }
  }, [chatUrl, input, messages, pending])

  return (
    <section
      id="chat"
      className="flex w-full max-w-2xl min-h-0 flex-1 flex-col justify-center"
      aria-label="Chat"
    >
      <GlassSurface className="flex max-h-[min(85dvh,40rem)] min-h-[min(60dvh,28rem)] flex-col gap-4 p-5 md:p-6">
        <div className="flex items-center gap-3 border-b border-white/10 pb-4">
          <LobeHub.Combine
            size={34}
            type="color"
            className="shrink-0 drop-shadow-md drop-shadow-black/30 [&_svg]:flex-none"
          />
          <h2 className="text-lg font-semibold tracking-tight text-white/90">Chat</h2>
        </div>
        <p className="text-xs text-white/45">
          {base ? (
            <>
              API: <code className="rounded bg-white/10 px-1">{chatUrl}</code>
            </>
          ) : (
            <>
              Same-origin <code className="rounded bg-white/10 px-1">POST /api/chat</code>{' '}
              (root Vercel deploy). For a standalone SPA, set{' '}
              <code className="rounded bg-white/10 px-1">VITE_CHAT_API_BASE</code>.
            </>
          )}
        </p>
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto rounded-xl bg-black/25 p-3 text-sm ring-1 ring-white/10">
          {messages.length === 0 ? (
            <p className="text-white/45">Ask anything about code…</p>
          ) : (
            messages.map((m, i) => (
              <div
                key={`${i}-${m.role}`}
                className={
                  m.role === 'user'
                    ? 'ml-8 rounded-lg bg-white/12 px-3 py-2 text-white/95'
                    : 'mr-8 rounded-lg bg-white/6 px-3 py-2 text-white/85'
                }
              >
                <span className="mb-1 block text-[10px] uppercase tracking-wider text-white/40">
                  {m.role}
                </span>
                <div className="whitespace-pre-wrap">{m.content}</div>
              </div>
            ))
          )}
        </div>
        {error ? (
          <p className="text-sm text-red-300/95">{error}</p>
        ) : null}
        <div className="flex flex-col gap-2 sm:flex-row">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                void send()
              }
            }}
            placeholder="Message… (Enter send, Shift+Enter newline)"
            rows={2}
            className="min-h-[44px] flex-1 resize-none rounded-xl border border-white/15 bg-black/30 px-3 py-2 text-sm text-white placeholder:text-white/35 focus:border-violet-400/50 focus:outline-none focus:ring-1 focus:ring-violet-400/30"
          />
          <button
            type="button"
            disabled={pending}
            onClick={() => void send()}
            className="rounded-xl bg-white/90 px-5 py-2.5 text-sm font-semibold text-neutral-950 shadow-lg shadow-black/20 ring-1 ring-white/25 transition hover:bg-white disabled:opacity-45"
          >
            {pending ? '…' : 'Send'}
          </button>
        </div>
      </GlassSurface>
    </section>
  )
}

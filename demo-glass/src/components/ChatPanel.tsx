import { useRef, useState } from 'react'
import { GlassSurface } from './GlassSurface'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

const API_BASE =
  (import.meta.env.VITE_CHAT_API_BASE as string | undefined) ||
  'https://mini-claude-code.vercel.app'

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([])
  const [history, setHistory] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  async function send() {
    const text = input.trim()
    if (!text || loading) return
    setInput('')
    setError(null)

    const userMsg: Message = { role: 'user', content: text }
    setMessages((m) => [...m, userMsg])
    setLoading(true)

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history, new_message: text }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error((err as { detail?: string }).detail || `HTTP ${res.status}`)
      }
      const data = (await res.json()) as { response: string; messages: Message[] }
      setHistory(data.messages)
      setMessages((m) => [...m, { role: 'assistant', content: data.response }])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong')
    } finally {
      setLoading(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)
    }
  }

  return (
    <section id="chat" className="w-full max-w-3xl scroll-mt-28 mx-auto">
      <p className="mb-4 text-xs font-medium uppercase tracking-[0.28em] text-white/45 text-center">
        AI Chat
      </p>
      <h2 className="text-2xl font-semibold tracking-tight text-center mb-8">
        Ask anything about code
      </h2>

      <GlassSurface className="flex flex-col gap-0 overflow-hidden p-0">
        {/* Message list */}
        <div className="flex flex-col gap-3 p-5 min-h-[280px] max-h-[420px] overflow-y-auto">
          {messages.length === 0 && (
            <div className="flex flex-1 items-center justify-center text-white/35 text-sm py-10 text-center">
              Debug errors · explain concepts · review code
            </div>
          )}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                  m.role === 'user'
                    ? 'bg-white/20 text-white'
                    : 'bg-white/8 text-white/90 border border-white/10'
                }`}
              >
                <span className="block text-[10px] font-medium mb-1 opacity-50 uppercase tracking-wide">
                  {m.role === 'user' ? 'You' : 'Assistant'}
                </span>
                {m.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white/8 border border-white/10 rounded-2xl px-4 py-3 text-sm text-white/50 italic">
                Thinking…
              </div>
            </div>
          )}
          {error && (
            <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-2.5 text-sm text-red-300">
              {error}
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Divider */}
        <div className="border-t border-white/10" />

        {/* Input row */}
        <div className="flex gap-3 p-4">
          <textarea
            rows={1}
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              e.target.style.height = 'auto'
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                send()
              }
            }}
            placeholder="Ask about code… (Enter to send)"
            className="flex-1 resize-none bg-transparent text-white text-sm placeholder-white/30 outline-none leading-relaxed py-1"
          />
          <button
            onClick={send}
            disabled={loading || !input.trim()}
            className="self-end rounded-full bg-white/20 px-5 py-2 text-sm font-medium text-white transition hover:bg-white/30 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </GlassSurface>
    </section>
  )
}

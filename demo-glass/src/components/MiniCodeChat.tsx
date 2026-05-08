import { LobeHub } from '@lobehub/icons'
import { useCallback, useMemo, useRef, useState } from 'react'
import { AlertTriangle, Bot, CheckCircle2, Code2, Sparkles, UserRound } from 'lucide-react'
import { GlassSurface } from './GlassSurface'
import {
  ClaudeChatInput,
} from './ClaudeChatInput'
import {
  LargePromptPlan,
  createPromptPlan,
  shouldCreatePromptPlan,
  type PromptPlan,
} from './LargePromptPlan'
import { formatFileSize, type ChatSendPayload } from './chatComposerTypes'

type ChatMsg = { role: 'user' | 'assistant'; content: string; plan?: PromptPlan }

const EMPTY_PROMPTS = [
  'Debug a failing API response',
  'Explain unfamiliar code',
  'Draft tests for a component',
]

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
  const promptPlansRef = useRef(new Map<string, PromptPlan>())

  const addPlansToMessages = useCallback((incomingMessages: ChatMsg[]) => {
    return incomingMessages.map((message) => {
      if (message.role !== 'user') return message
      const plan = promptPlansRef.current.get(message.content)
      return plan ? { ...message, plan } : message
    })
  }, [])

  const onSendMessage = useCallback(
    async (payload: ChatSendPayload) => {
      if (sendingRef.current) return
      sendingRef.current = true
      setPending(true)
      setError(null)
      try {
        const text = await buildNewMessage(payload)
        if (!text) return
        const plan = shouldCreatePromptPlan(text) ? createPromptPlan(text) : undefined
        if (plan) promptPlansRef.current.set(text, plan)
        setMessages((current) => [...current, { role: 'user', content: text, plan }])

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
          setMessages(addPlansToMessages(data.messages))
        } else if (data.response) {
          setMessages((current) => [...current, { role: 'assistant', content: data.response }])
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Request failed')
      } finally {
        sendingRef.current = false
        setPending(false)
      }
    },
    [addPlansToMessages, chatUrl, messages]
  )

  return (
    <section
      id="chat"
      className="flex w-full max-w-3xl min-h-0 flex-1 flex-col justify-center gap-5"
      aria-label="Chat"
    >
      <div className="space-y-3 text-center">
        <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/[0.07] px-3 py-1 text-xs font-medium text-white/70 shadow-[0_1px_0_rgba(255,255,255,0.12)_inset] backdrop-blur-xl">
          <Sparkles className="h-3.5 w-3.5 text-violet-200" aria-hidden />
          Local model UI
        </div>
        <div className="space-y-2">
          <h1 className="text-balance text-3xl font-semibold tracking-[-0.04em] text-white sm:text-5xl">
            Ask anything about code.
          </h1>
          <p className="mx-auto max-w-xl text-sm leading-6 text-white/50 sm:text-base">
            A focused glass workspace for debugging, learning, reviewing, and shipping with AI.
          </p>
        </div>
      </div>

      <GlassSurface className="relative flex max-h-[min(50dvh,27rem)] min-h-[17rem] flex-col overflow-hidden p-0">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-white/[0.08] to-transparent" />
        <div className="relative flex shrink-0 items-center justify-between gap-3 border-b border-white/10 px-4 py-3 md:px-5">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl border border-white/12 bg-white/[0.08] shadow-[0_1px_0_rgba(255,255,255,0.12)_inset]">
              <LobeHub.Combine
                size={30}
                type="color"
                className="drop-shadow-md drop-shadow-black/30 [&_svg]:flex-none"
              />
            </div>
            <div className="min-w-0 text-left">
              <h2 className="truncate text-sm font-semibold tracking-tight text-white/92">
                Code companion
              </h2>
              <p className="truncate text-xs text-white/42">
                Attach files, paste context, or start with a quick prompt.
              </p>
            </div>
          </div>
          <div className="hidden items-center gap-1.5 rounded-full border border-emerald-300/18 bg-emerald-400/8 px-2.5 py-1 text-xs font-medium text-emerald-100/75 sm:flex">
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden />
            Ready
          </div>
        </div>

        <div className="custom-scrollbar relative min-h-0 flex-1 space-y-3 overflow-y-auto p-4 text-sm md:p-5">
          {messages.length === 0 ? (
            <div className="flex min-h-full flex-col items-center justify-center py-6 text-center">
              <div className="mb-4 grid h-14 w-14 place-items-center rounded-3xl border border-white/12 bg-white/[0.07] shadow-[0_16px_50px_rgba(0,0,0,0.22)]">
                <Code2 className="h-6 w-6 text-violet-100/90" aria-hidden />
              </div>
              <p className="text-base font-medium text-white/88">What are we building today?</p>
              <p className="mt-1 max-w-sm text-sm leading-6 text-white/42">
                Start from a question, attach code, or use one of the shortcuts below.
              </p>
              <div className="mt-5 flex flex-wrap justify-center gap-2">
                {EMPTY_PROMPTS.map((prompt) => (
                  <span
                    key={prompt}
                    className="rounded-full border border-white/10 bg-white/[0.06] px-3 py-1.5 text-xs text-white/58"
                  >
                    {prompt}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            messages.map((m, i) => (
              <div
                key={`${i}-${m.role}`}
                className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.role === 'assistant' ? (
                  <div className="mt-1 grid h-7 w-7 shrink-0 place-items-center rounded-full border border-white/10 bg-white/[0.07]">
                    <Bot className="h-3.5 w-3.5 text-white/65" aria-hidden />
                  </div>
                ) : null}
                <div
                  className={
                    m.role === 'user'
                      ? 'max-w-[86%] rounded-[1.2rem] rounded-tr-md bg-gradient-to-br from-violet-400/24 to-fuchsia-400/16 px-4 py-3 text-white/95 shadow-[0_10px_28px_rgba(0,0,0,0.18)] ring-1 ring-white/12'
                      : 'max-w-[86%] rounded-[1.2rem] rounded-tl-md border border-white/10 bg-white/[0.055] px-4 py-3 text-white/86 shadow-[0_10px_28px_rgba(0,0,0,0.16)]'
                  }
                >
                  <span className="mb-1.5 block text-[10px] font-semibold uppercase tracking-[0.18em] text-white/38">
                    {m.role === 'user' ? 'You' : 'Assistant'}
                  </span>
                  <div className="whitespace-pre-wrap leading-6">{m.content}</div>
                  {m.plan ? <LargePromptPlan plan={m.plan} /> : null}
                </div>
                {m.role === 'user' ? (
                  <div className="mt-1 grid h-7 w-7 shrink-0 place-items-center rounded-full border border-violet-200/18 bg-violet-300/12">
                    <UserRound className="h-3.5 w-3.5 text-violet-100/80" aria-hidden />
                  </div>
                ) : null}
              </div>
            ))
          )}
          {pending ? (
            <div className="flex items-center gap-2 text-sm text-white/48">
              <span className="h-2 w-2 animate-pulse rounded-full bg-violet-300" />
              Thinking through your request...
            </div>
          ) : null}
          {error ? (
            <div className="flex items-start gap-3 rounded-2xl border border-red-300/20 bg-red-500/10 px-4 py-3 text-left text-sm text-red-100/85">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-200" aria-hidden />
              <div>
                <p className="font-medium">Request failed</p>
                <p className="mt-0.5 text-red-100/70">{error}</p>
              </div>
            </div>
          ) : null}
        </div>
      </GlassSurface>

      <ClaudeChatInput disabled={pending} onSendMessage={onSendMessage} />
    </section>
  )
}

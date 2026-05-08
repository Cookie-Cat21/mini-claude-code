import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type ClipboardEvent,
  type DragEvent,
  type SVGProps,
} from 'react'
import {
  Plus,
  ChevronDown,
  ArrowUp,
  X,
  FileText,
  Loader2,
  Check,
  Archive,
  PenLine,
  GraduationCap,
  Brackets,
  Home,
  type LucideIcon,
} from 'lucide-react'
import { formatFileSize } from './chatComposerTypes'
import type { AttachedFile, ChatModel, ChatSendPayload, PastedSnippet } from './chatComposerTypes'

function ThinkingIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 20 20"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
      {...props}
    >
      <path d="M10.3857 2.50977C14.3486 2.71054 17.5 5.98724 17.5 10C17.5 14.1421 14.1421 17.5 10 17.5C5.85786 17.5 2.5 14.1421 2.5 10C2.5 9.72386 2.72386 9.5 3 9.5C3.27614 9.5 3.5 9.72386 3.5 10C3.5 13.5899 6.41015 16.5 10 16.5C13.5899 16.5 16.5 13.5899 16.5 10C16.5 6.5225 13.7691 3.68312 10.335 3.50879L10 3.5L9.89941 3.49023C9.67145 3.44371 9.5 3.24171 9.5 3C9.5 2.72386 9.72386 2.5 10 2.5L10.3857 2.50977ZM10 5.5C10.2761 5.5 10.5 5.72386 10.5 6V9.69043L13.2236 11.0527C13.4706 11.1762 13.5708 11.4766 13.4473 11.7236C13.3392 11.9397 13.0957 12.0435 12.8711 11.9834L12.7764 11.9473L9.77637 10.4473C9.60698 10.3626 9.5 10.1894 9.5 10V6C9.5 5.72386 9.72386 5.5 10 5.5ZM3.66211 6.94141C4.0273 6.94159 4.32303 7.23735 4.32324 7.60254C4.32324 7.96791 4.02743 8.26446 3.66211 8.26465C3.29663 8.26465 3 7.96802 3 7.60254C3.00021 7.23723 3.29676 6.94141 3.66211 6.94141ZM4.95605 4.29395C5.32146 4.29404 5.61719 4.59063 5.61719 4.95605C5.6171 5.3214 5.3214 5.61709 4.95605 5.61719C4.59063 5.61719 4.29403 5.32146 4.29395 4.95605C4.29395 4.59057 4.59057 4.29395 4.95605 4.29395ZM7.60254 3C7.96802 3 8.26465 3.29663 8.26465 3.66211C8.26446 4.02743 7.96791 4.32324 7.60254 4.32324C7.23736 4.32302 6.94159 4.0273 6.94141 3.66211C6.94141 3.29676 7.23724 3.00022 7.60254 3Z" />
    </svg>
  )
}

interface FilePreviewCardProps {
  file: AttachedFile
  onRemove: (id: string) => void
}

const FilePreviewCard = ({ file, onRemove }: FilePreviewCardProps) => {
  const isImage = file.type.startsWith('image/') && file.preview

  return (
    <div
      className="group relative flex h-24 w-24 shrink-0 animate-fade-in overflow-hidden rounded-xl border border-white/20 bg-white/5 transition-all hover:border-white/35"
    >
      {isImage ? (
        <div className="relative h-full w-full">
          <img src={file.preview!} alt={file.file.name} className="h-full w-full object-cover" />
          <div className="absolute inset-0 bg-black/20 transition-colors group-hover:bg-black/0" />
        </div>
      ) : (
        <div className="flex h-full w-full flex-col justify-between p-3">
          <div className="flex items-center gap-2">
            <div className="rounded bg-white/10 p-1.5">
              <FileText className="h-4 w-4 text-white/55" />
            </div>
            <span className="truncate text-[10px] font-medium uppercase tracking-wider text-white/45">
              {file.file.name.split('.').pop()}
            </span>
          </div>
          <div className="space-y-0.5">
            <p className="truncate text-xs font-medium text-white/90" title={file.file.name}>
              {file.file.name}
            </p>
            <p className="text-[10px] text-white/45">{formatFileSize(file.file.size)}</p>
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={() => onRemove(file.id)}
        className="absolute right-1 top-1 rounded-full bg-black/50 p-1 text-white opacity-0 transition-opacity hover:bg-black/70 group-hover:opacity-100"
      >
        <X className="h-3 w-3" />
      </button>

      {file.uploadStatus === 'uploading' ? (
        <div className="absolute inset-0 flex items-center justify-center bg-black/40">
          <Loader2 className="h-5 w-5 animate-spin text-white" />
        </div>
      ) : null}
    </div>
  )
}

interface PastedContentCardProps {
  snippet: PastedSnippet
  onRemove: (id: string) => void
}

const PastedContentCard = ({ snippet, onRemove }: PastedContentCardProps) => {
  return (
    <div className="group relative flex h-28 w-28 shrink-0 animate-fade-in flex-col justify-between overflow-hidden rounded-2xl border border-white/15 bg-black/30 p-3 shadow-[0_1px_2px_rgba(0,0,0,0.2)]">
      <div className="w-full overflow-hidden">
        <p className="line-clamp-4 select-none whitespace-pre-wrap break-words font-mono text-[10px] leading-[1.4] text-white/45">
          {snippet.content}
        </p>
      </div>

      <div className="mt-2 flex w-full items-center justify-between">
        <div className="inline-flex items-center justify-center rounded border border-white/15 bg-black/20 px-1.5 py-0.5">
          <span className="font-sans text-[9px] font-bold uppercase tracking-wider text-white/50">
            pasted
          </span>
        </div>
      </div>

      <button
        type="button"
        onClick={() => onRemove(snippet.id)}
        className="absolute right-2 top-2 rounded-full border border-white/15 bg-zinc-900/90 p-[3px] text-white/45 opacity-0 shadow-sm transition-all hover:text-white group-hover:opacity-100"
      >
        <X className="h-2 w-2" />
      </button>
    </div>
  )
}

interface ModelSelectorProps {
  models: ChatModel[]
  selectedModel: string
  onSelect: (modelId: string) => void
  disabled?: boolean
}

const ModelSelector = ({ models, selectedModel, onSelect, disabled }: ModelSelectorProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const currentModel = models.find((m) => m.id === selectedModel) ?? models[0]

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen((o) => !o)}
        className={`inline-flex h-8 min-w-[4rem] shrink-0 items-center justify-center gap-1 rounded-xl px-2.5 pl-2.5 pr-2 text-xs font-medium whitespace-nowrap transition active:scale-[0.98] disabled:opacity-45 ${
          isOpen
            ? 'bg-white/15 text-white'
            : 'text-white/55 hover:bg-white/10 hover:text-white'
        }`}
      >
        <span className="select-none text-[14px] leading-none">{currentModel.name}</span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 opacity-75 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
        />
      </button>

      {isOpen ? (
        <div className="absolute bottom-full right-0 z-50 mb-2 flex w-[260px] origin-bottom-right flex-col overflow-hidden rounded-2xl border border-white/15 bg-zinc-900/98 p-1.5 shadow-2xl backdrop-blur-md animate-fade-in">
          {models.map((model) => (
            <button
              key={model.id}
              type="button"
              onClick={() => {
                onSelect(model.id)
                setIsOpen(false)
              }}
              className="group flex w-full items-start justify-between rounded-xl px-3 py-2.5 text-left transition-colors hover:bg-white/10"
            >
              <div className="flex flex-col gap-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-[13px] font-semibold text-white">{model.name}</span>
                  {model.badge ? (
                    <span
                      className={`rounded-full border px-1.5 py-px text-[10px] font-medium ${
                        model.badge === 'Upgrade'
                          ? 'border-blue-400/40 bg-blue-500/15 text-blue-300'
                          : 'border-white/15 text-white/55'
                      }`}
                    >
                      {model.badge}
                    </span>
                  ) : null}
                </div>
                <span className="text-[11px] text-white/45">{model.description}</span>
              </div>
              {selectedModel === model.id ? (
                <Check className="mt-1 h-4 w-4 shrink-0 text-violet-400" />
              ) : null}
            </button>
          ))}

          <div className="mx-2 my-1 h-px bg-white/10" />

          <button
            type="button"
            className="flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left text-white transition-colors hover:bg-white/10"
            onClick={() => setIsOpen(false)}
          >
            <span className="text-[13px] font-semibold">More models</span>
            <ChevronDown className="h-4 w-4 -rotate-90 text-white/45" />
          </button>
        </div>
      ) : null}
    </div>
  )
}

const DEFAULT_MODELS: ChatModel[] = [
  { id: 'opus-4.5', name: 'Opus 4.5', description: 'Most capable for complex work' },
  { id: 'sonnet-4.5', name: 'Sonnet 4.5', description: 'Best for everyday tasks' },
  { id: 'haiku-4.5', name: 'Haiku 4.5', description: 'Fastest for quick answers' },
]

const QUICK_ACTIONS: { id: string; label: string; icon: LucideIcon; prompt: string }[] = [
  { id: 'write', label: 'Write', icon: PenLine, prompt: 'Help me write:\n\n' },
  {
    id: 'learn',
    label: 'Learn',
    icon: GraduationCap,
    prompt: 'Explain this so I can learn it:\n\n',
  },
  {
    id: 'code',
    label: 'Code',
    icon: Brackets,
    prompt: 'Help with this code:\n\n```\n\n```',
  },
  {
    id: 'life',
    label: 'Life stuff',
    icon: Home,
    prompt: "I'd like perspective on a life situation:\n\n",
  },
]

interface ClaudeChatInputProps {
  onSendMessage: (data: ChatSendPayload) => void
  disabled?: boolean
  models?: ChatModel[]
}

export function ClaudeChatInput({
  onSendMessage,
  disabled = false,
  models = DEFAULT_MODELS,
}: ClaudeChatInputProps) {
  const [message, setMessage] = useState('')
  const [files, setFiles] = useState<AttachedFile[]>([])
  const [pastedSnippets, setPastedSnippets] = useState<PastedSnippet[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [selectedModel, setSelectedModel] = useState(models[1]?.id ?? models[0].id)
  const [isThinkingEnabled, setIsThinkingEnabled] = useState(false)

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 384)}px`
  }, [message])

  const handleFiles = useCallback((newFilesList: FileList | File[]) => {
    const newFiles: AttachedFile[] = Array.from(newFilesList).map((file) => {
      const isImage =
        file.type.startsWith('image/') || /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(file.name)
      return {
        id: Math.random().toString(36).slice(2, 11),
        file,
        type: isImage ? 'image/unknown' : file.type || 'application/octet-stream',
        preview: isImage ? URL.createObjectURL(file) : null,
        uploadStatus: 'uploading',
      }
    })

    setFiles((prev) => [...prev, ...newFiles])

    setMessage((prev) => {
      if (prev) return prev
      if (newFiles.length === 1) {
        const f = newFiles[0]
        if (f.type.startsWith('image/')) return 'Analyzed image…'
        return 'Analyzed document…'
      }
      return `Analyzed ${newFiles.length} files…`
    })

    newFiles.forEach((f) => {
      window.setTimeout(() => {
        setFiles((prev) =>
          prev.map((p) => (p.id === f.id ? { ...p, uploadStatus: 'complete' } : p))
        )
      }, 800 + Math.random() * 400)
    })
  }, [])

  const onDragOver = (e: DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }
  const onDragLeave = (e: DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }
  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files?.length) handleFiles(e.dataTransfer.files)
  }

  const handlePaste = (e: ClipboardEvent) => {
    const items = e.clipboardData.items
    const pastedFiles: File[] = []
    for (let i = 0; i < items.length; i++) {
      if (items[i].kind === 'file') {
        const file = items[i].getAsFile()
        if (file) pastedFiles.push(file)
      }
    }

    if (pastedFiles.length > 0) {
      e.preventDefault()
      handleFiles(pastedFiles)
      return
    }

    const text = e.clipboardData.getData('text')
    if (text.length > 300) {
      e.preventDefault()
      const snippet: PastedSnippet = {
        id: Math.random().toString(36).slice(2, 11),
        content: text,
        timestamp: new Date(),
      }
      setPastedSnippets((prev) => [...prev, snippet])
      if (!message) setMessage('Analyzed pasted text…')
    }
  }

  const handleSend = () => {
    if (
      !message.trim() &&
      files.length === 0 &&
      pastedSnippets.length === 0
    )
      return
    if (disabled) return
    onSendMessage({
      message,
      files,
      pastedContent: pastedSnippets,
      model: selectedModel,
      isThinkingEnabled,
    })
    setMessage('')
    setFiles([])
    setPastedSnippets([])
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const applyQuickAction = useCallback(
    (prompt: string) => {
      if (disabled) return
      setMessage((prev) => {
        const t = prev.trim()
        return t ? `${t}\n\n${prompt}` : prompt
      })
      window.setTimeout(() => {
        const el = textareaRef.current
        if (!el) return
        el.focus()
        const len = el.value.length
        el.setSelectionRange(len, len)
      }, 0)
    },
    [disabled]
  )

  const hasContent =
    Boolean(message.trim()) || files.length > 0 || pastedSnippets.length > 0

  return (
    <div
      className="relative mx-auto w-full max-w-2xl font-sans transition-all duration-300"
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <div
        className="relative z-10 mx-2 flex cursor-text flex-col items-stretch overflow-hidden rounded-[1.65rem] border border-white/14 bg-[#101016]/82 shadow-[0_24px_80px_rgba(0,0,0,0.38),inset_0_1px_0_rgba(255,255,255,0.1)] backdrop-blur-2xl transition-all duration-200 before:pointer-events-none before:absolute before:inset-x-0 before:top-0 before:h-px before:bg-gradient-to-r before:from-transparent before:via-white/35 before:to-transparent focus-within:border-violet-200/28 focus-within:shadow-[0_28px_90px_rgba(0,0,0,0.45),0_0_0_1px_rgba(196,181,253,0.12)] hover:border-white/20 md:mx-0"
      >
        <div className="flex flex-col gap-2 px-3.5 pt-3.5 pb-3">
          {files.length > 0 || pastedSnippets.length > 0 ? (
            <div className="custom-scrollbar flex gap-3 overflow-x-auto px-1 pb-2">
              {pastedSnippets.map((s) => (
                <PastedContentCard
                  key={s.id}
                  snippet={s}
                  onRemove={(id) =>
                    setPastedSnippets((prev) => prev.filter((c) => c.id !== id))
                  }
                />
              ))}
              {files.map((f) => (
                <FilePreviewCard
                  key={f.id}
                  file={f}
                  onRemove={(id) => setFiles((prev) => prev.filter((x) => x.id !== id))}
                />
              ))}
            </div>
          ) : null}

          <div className="relative mb-1">
            <div className="custom-scrollbar max-h-96 min-h-[2.65rem] w-full overflow-y-auto px-1 font-sans break-words transition-opacity duration-200">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onPaste={handlePaste}
                onKeyDown={handleKeyDown}
                placeholder="How can I help you today?"
                rows={1}
                disabled={disabled}
                className="block w-full resize-none overflow-hidden border-0 bg-transparent py-0.5 text-[16px] leading-relaxed font-normal text-white antialiased outline-none placeholder:text-white/42 disabled:opacity-45"
                style={{ minHeight: '1.5em' }}
              />
            </div>
          </div>

          <div className="flex w-full items-center gap-2 border-t border-white/[0.07] pt-2">
            <div className="relative flex min-w-0 flex-1 shrink items-center gap-1">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={disabled}
                className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-white/50 transition-colors duration-200 hover:bg-white/10 hover:text-white active:scale-95 disabled:opacity-45"
                aria-label="Attach files"
              >
                <Plus className="h-5 w-5" />
              </button>

              <div className="relative flex shrink-0">
                <button
                  type="button"
                  onClick={() => setIsThinkingEnabled((v) => !v)}
                  disabled={disabled}
                  className={`group relative flex h-8 w-8 items-center justify-center rounded-xl transition-all duration-200 active:scale-95 disabled:opacity-45 ${
                    isThinkingEnabled
                      ? 'bg-violet-400/18 text-violet-100 ring-1 ring-violet-200/20'
                      : 'text-white/45 hover:bg-white/10 hover:text-white'
                  }`}
                  aria-pressed={isThinkingEnabled}
                  aria-label="Extended thinking"
                >
                  <ThinkingIcon className="h-5 w-5" />
                  <span className="pointer-events-none absolute top-full left-1/2 z-50 mt-2 flex -translate-x-1/2 items-center gap-1 whitespace-nowrap rounded-md bg-zinc-950 px-2 py-1 text-[11px] font-medium tracking-wide text-white opacity-0 shadow-sm transition-opacity group-hover:opacity-100">
                    Extended thinking
                    <span className="text-[10px] text-white/55">⇧⌃E</span>
                  </span>
                </button>
              </div>
            </div>

            <div className="flex min-w-0 flex-row items-center gap-1">
              <div className="-m-1 shrink-0 p-1">
                <ModelSelector
                  models={models}
                  selectedModel={selectedModel}
                  onSelect={setSelectedModel}
                  disabled={disabled}
                />
              </div>

              <button
                type="button"
                onClick={handleSend}
                disabled={!hasContent || disabled}
                className={`inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl transition-all active:scale-95 ${
                  hasContent && !disabled
                    ? 'bg-gradient-to-b from-violet-400 to-violet-600 text-white shadow-[0_8px_22px_rgba(124,58,237,0.35)] hover:brightness-110'
                    : 'cursor-default bg-white/[0.08] text-white/34'
                }`}
                aria-label="Send message"
              >
                <ArrowUp className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {isDragging ? (
        <div className="pointer-events-none absolute inset-0 z-50 flex flex-col items-center justify-center rounded-[1.65rem] border-2 border-dashed border-violet-300/80 bg-zinc-950/88 backdrop-blur-md">
          <Archive className="mb-2 h-10 w-10 animate-bounce text-violet-400" />
          <p className="font-medium text-violet-300">Drop files to upload</p>
        </div>
      ) : null}

      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={(e) => {
          if (e.target.files?.length) handleFiles(e.target.files)
          e.target.value = ''
        }}
      />

      <p className="mt-4 text-center text-xs text-white/38">
        AI can make mistakes. Please check important information.
      </p>

      <div
        className="mt-3 flex flex-wrap items-center justify-center gap-2 px-1"
        role="toolbar"
        aria-label="Quick prompts"
      >
        {QUICK_ACTIONS.map(({ id, label, icon: Icon, prompt }) => (
          <button
            key={id}
            type="button"
            disabled={disabled}
            onClick={() => applyQuickAction(prompt)}
            className="inline-flex items-center gap-1.5 rounded-full border border-white/14 bg-white/[0.07] px-3.5 py-1.5 text-xs font-medium text-white/76 shadow-[0_1px_0_rgba(255,255,255,0.08)_inset,0_10px_28px_rgba(0,0,0,0.16)] backdrop-blur-xl transition hover:border-violet-200/28 hover:bg-violet-300/10 hover:text-white active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-45"
          >
            <Icon className="h-3.5 w-3.5 shrink-0 opacity-90" aria-hidden />
            {label}
          </button>
        ))}
      </div>

      <p className="mt-3 text-center text-[11px] text-white/30">
        Model UI is local — the server picks the Groq model.
      </p>
    </div>
  )
}

export default ClaudeChatInput

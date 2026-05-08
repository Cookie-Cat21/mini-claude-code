import { useMemo, useState } from 'react'
import {
  CheckCircle2,
  ChevronRight,
  Circle,
  CircleAlert,
  CircleDotDashed,
  CircleX,
  Wrench,
  type LucideIcon,
} from 'lucide-react'

type PlanStatus = 'completed' | 'in-progress' | 'pending' | 'need-help' | 'failed'
type PlanPriority = 'high' | 'medium' | 'low'

export interface PlanSubtask {
  id: string
  title: string
  description: string
  status: PlanStatus
  priority: PlanPriority
  tools?: string[]
}

export interface PlanTask {
  id: string
  title: string
  description: string
  status: PlanStatus
  priority: PlanPriority
  level: number
  dependencies: string[]
  subtasks: PlanSubtask[]
}

export interface PromptPlan {
  title: string
  summary: string
  tasks: PlanTask[]
}

const LARGE_PROMPT_MIN_CHARS = 900
const LARGE_PROMPT_MIN_LINES = 12

const STATUS_STYLES: Record<
  PlanStatus,
  { label: string; icon: LucideIcon; iconClass: string; badgeClass: string }
> = {
  completed: {
    label: 'completed',
    icon: CheckCircle2,
    iconClass: 'text-emerald-300',
    badgeClass: 'border-emerald-300/20 bg-emerald-400/10 text-emerald-100/80',
  },
  'in-progress': {
    label: 'in progress',
    icon: CircleDotDashed,
    iconClass: 'text-sky-300',
    badgeClass: 'border-sky-300/20 bg-sky-400/10 text-sky-100/80',
  },
  pending: {
    label: 'pending',
    icon: Circle,
    iconClass: 'text-white/38',
    badgeClass: 'border-white/10 bg-white/[0.06] text-white/48',
  },
  'need-help': {
    label: 'needs input',
    icon: CircleAlert,
    iconClass: 'text-amber-300',
    badgeClass: 'border-amber-300/20 bg-amber-400/10 text-amber-100/80',
  },
  failed: {
    label: 'blocked',
    icon: CircleX,
    iconClass: 'text-red-300',
    badgeClass: 'border-red-300/20 bg-red-400/10 text-red-100/80',
  },
}

const PRIORITY_STYLES: Record<PlanPriority, string> = {
  high: 'border-violet-200/20 bg-violet-300/10 text-violet-100/80',
  medium: 'border-white/10 bg-white/[0.06] text-white/58',
  low: 'border-white/8 bg-white/[0.04] text-white/42',
}

const normalizeLine = (line: string) =>
  line
    .replace(/^\s*(?:[-*+]|\d+[.)]|\[[ xX-]\])\s+/, '')
    .replace(/^#{1,6}\s+/, '')
    .trim()

const toTitle = (text: string, fallback: string) => {
  const cleaned = normalizeLine(text).replace(/[`*_>#]/g, '').trim()
  if (!cleaned) return fallback
  return cleaned.length > 68 ? `${cleaned.slice(0, 65).trim()}...` : cleaned
}

const sentenceFrom = (text: string, fallback: string) => {
  const cleaned = text.replace(/\s+/g, ' ').trim()
  if (!cleaned) return fallback
  const end = cleaned.search(/[.!?]\s/)
  const sentence = end > 24 ? cleaned.slice(0, end + 1) : cleaned
  return sentence.length > 150 ? `${sentence.slice(0, 147).trim()}...` : sentence
}

const unique = (items: string[]) => Array.from(new Set(items))

const inferTools = (prompt: string) => {
  const lower = prompt.toLowerCase()
  const tools: string[] = []
  if (/\b(api|endpoint|server|backend|fetch)\b/.test(lower)) tools.push('api-client')
  if (/\b(component|ui|react|tsx|css|tailwind)\b/.test(lower)) tools.push('ui-builder')
  if (/\b(test|spec|coverage|verify|bug|error)\b/.test(lower)) tools.push('test-runner')
  if (/\b(database|schema|sql|postgres|redis|storage)\b/.test(lower)) tools.push('data-inspector')
  if (/\bdeploy|vercel|ci|workflow|github action\b/.test(lower)) tools.push('deployment-checker')
  return tools.length > 0 ? unique(tools) : ['code-assistant']
}

export function shouldCreatePromptPlan(prompt: string) {
  const trimmed = prompt.trim()
  if (!trimmed) return false
  const lineCount = trimmed.split(/\r?\n/).filter((line) => line.trim()).length
  return trimmed.length >= LARGE_PROMPT_MIN_CHARS || lineCount >= LARGE_PROMPT_MIN_LINES
}

export function createPromptPlan(prompt: string): PromptPlan {
  const lines = prompt
    .split(/\r?\n/)
    .map(normalizeLine)
    .filter(Boolean)
    .filter((line) => !/^\[(?:pasted content|file:|attached file:|attached image:)/i.test(line))
    .filter((line) => line.length > 5 && !/^```/.test(line))

  const signalLines = lines.filter((line) =>
    /^(add|build|create|fix|implement|update|design|review|verify|test|make|wire|refactor|support|ensure|investigate)\b/i.test(
      line
    )
  )
  const sourceGoals = (signalLines.length > 0 ? signalLines : lines).slice(0, 5)
  const goals = sourceGoals.length > 0 ? sourceGoals : ['Handle the requested change end-to-end']
  const tools = inferTools(prompt)

  const taskTemplates = [
    {
      title: 'Understand the requested outcome',
      description: sentenceFrom(prompt, 'Identify the desired behavior and constraints from the prompt.'),
      priority: 'high' as const,
      subtasks: [
        'Extract acceptance criteria',
        'Identify affected surfaces',
        'Call out unknowns or dependencies',
      ],
    },
    {
      title: goals[0] ? toTitle(goals[0], 'Plan the main implementation path') : 'Plan the main implementation path',
      description: sentenceFrom(goals[0] ?? prompt, 'Break the primary request into implementation steps.'),
      priority: 'high' as const,
      subtasks: goals.slice(0, 3).map((goal) => toTitle(goal, 'Implement requested behavior')),
    },
    {
      title: goals[1] ? toTitle(goals[1], 'Handle supporting requirements') : 'Handle supporting requirements',
      description: 'Cover follow-up details, edge cases, and integration points from the full prompt.',
      priority: 'medium' as const,
      subtasks: [
        ...(goals.length > 3
          ? goals.slice(3, 5).map((goal) => toTitle(goal, 'Address supporting requirement'))
          : ['Wire the UI state and data shape', 'Preserve existing behavior']),
        'Keep changes scoped to the chat experience',
      ],
    },
    {
      title: 'Verify and summarize the result',
      description: 'Run focused checks and produce a concise handoff once the implementation is complete.',
      priority: 'medium' as const,
      subtasks: ['Run lint or build checks', 'Exercise the large-prompt path', 'Summarize behavior and risks'],
    },
  ]

  const tasks: PlanTask[] = taskTemplates.map((task, taskIndex) => ({
    id: `${taskIndex + 1}`,
    title: task.title,
    description: task.description,
    status: taskIndex === 0 ? 'in-progress' : 'pending',
    priority: task.priority,
    level: taskIndex >= 2 ? 1 : 0,
    dependencies: taskIndex > 1 ? [`${taskIndex}`] : [],
    subtasks: task.subtasks.slice(0, 3).map((subtask, subtaskIndex) => ({
      id: `${taskIndex + 1}.${subtaskIndex + 1}`,
      title: subtask,
      description:
        subtaskIndex === 0
          ? 'This item is pulled from the large prompt and can be refined as the conversation continues.'
          : 'Track this step while turning the prompt into a concrete response.',
      status: taskIndex === 0 && subtaskIndex === 0 ? 'completed' : taskIndex === 0 ? 'in-progress' : 'pending',
      priority: subtaskIndex === 0 ? task.priority : 'medium',
      tools,
    })),
  }))

  const titleLine = lines.find((line) => line.length > 10) ?? 'Large prompt plan'

  return {
    title: toTitle(titleLine, 'Large prompt plan'),
    summary: `${prompt.trim().length.toLocaleString()} characters analyzed into ${tasks.length} work streams.`,
    tasks,
  }
}

interface StatusGlyphProps {
  status: PlanStatus
  className?: string
}

function StatusGlyph({ status, className = 'h-4 w-4' }: StatusGlyphProps) {
  const statusMeta = STATUS_STYLES[status]
  const Icon = statusMeta.icon
  return <Icon className={`${className} ${statusMeta.iconClass}`} aria-hidden />
}

interface LargePromptPlanProps {
  plan: PromptPlan
}

export function LargePromptPlan({ plan }: LargePromptPlanProps) {
  const defaultExpandedTasks = useMemo(() => plan.tasks.slice(0, 2).map((task) => task.id), [plan.tasks])
  const [expandedTasks, setExpandedTasks] = useState<string[]>(defaultExpandedTasks)
  const [expandedSubtasks, setExpandedSubtasks] = useState<Record<string, boolean>>({})

  const toggleTask = (taskId: string) => {
    setExpandedTasks((current) =>
      current.includes(taskId) ? current.filter((id) => id !== taskId) : [...current, taskId]
    )
  }

  const toggleSubtask = (taskId: string, subtaskId: string) => {
    const key = `${taskId}-${subtaskId}`
    setExpandedSubtasks((current) => ({ ...current, [key]: !current[key] }))
  }

  return (
    <div className="mt-3 overflow-hidden rounded-[1.15rem] border border-white/12 bg-zinc-950/36 shadow-[0_18px_44px_rgba(0,0,0,0.2)]">
      <div className="border-b border-white/10 bg-white/[0.045] px-4 py-3">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-violet-100/50">
              Large prompt plan
            </p>
            <h3 className="mt-1 truncate text-sm font-semibold text-white/90">{plan.title}</h3>
            <p className="mt-1 text-xs leading-5 text-white/42">{plan.summary}</p>
          </div>
          <div className="shrink-0 rounded-full border border-violet-200/18 bg-violet-300/10 px-2.5 py-1 text-[11px] font-medium text-violet-100/75">
            {plan.tasks.length} tasks
          </div>
        </div>
      </div>

      <ul className="space-y-1 p-2">
        {plan.tasks.map((task) => {
          const isExpanded = expandedTasks.includes(task.id)
          const statusMeta = STATUS_STYLES[task.status]

          return (
            <li key={task.id} className="rounded-2xl">
              <button
                type="button"
                onClick={() => toggleTask(task.id)}
                className="group flex w-full items-center gap-2 rounded-2xl px-2.5 py-2 text-left transition hover:bg-white/[0.055]"
              >
                <StatusGlyph status={task.status} />
                <div className="min-w-0 flex-1">
                  <div className="flex min-w-0 items-center gap-2">
                    <span className="truncate text-sm font-medium text-white/86">{task.title}</span>
                    <span
                      className={`hidden rounded-full border px-1.5 py-0.5 text-[10px] font-medium sm:inline-flex ${PRIORITY_STYLES[task.priority]}`}
                    >
                      {task.priority}
                    </span>
                  </div>
                  <p className="mt-0.5 line-clamp-1 text-xs text-white/38">{task.description}</p>
                </div>
                {task.dependencies.length > 0 ? (
                  <div className="hidden gap-1 sm:flex">
                    {task.dependencies.map((dependency) => (
                      <span
                        key={dependency}
                        className="rounded-full border border-white/10 bg-white/[0.05] px-1.5 py-0.5 text-[10px] text-white/42"
                      >
                        after {dependency}
                      </span>
                    ))}
                  </div>
                ) : null}
                <span
                  className={`hidden rounded-full border px-2 py-0.5 text-[10px] font-medium md:inline-flex ${statusMeta.badgeClass}`}
                >
                  {statusMeta.label}
                </span>
                <ChevronRight
                  className={`h-4 w-4 shrink-0 text-white/34 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                  aria-hidden
                />
              </button>

              {isExpanded ? (
                <div className="relative ml-5 border-l border-dashed border-white/12 pb-1 pl-4">
                  <ul className="space-y-1">
                    {task.subtasks.map((subtask) => {
                      const subtaskKey = `${task.id}-${subtask.id}`
                      const isSubtaskExpanded = Boolean(expandedSubtasks[subtaskKey])
                      const subtaskStatus = STATUS_STYLES[subtask.status]

                      return (
                        <li key={subtask.id}>
                          <button
                            type="button"
                            onClick={() => toggleSubtask(task.id, subtask.id)}
                            className="group flex w-full items-center gap-2 rounded-xl px-2 py-1.5 text-left transition hover:bg-white/[0.045]"
                          >
                            <StatusGlyph status={subtask.status} className="h-3.5 w-3.5" />
                            <span className="min-w-0 flex-1 truncate text-xs font-medium text-white/72">
                              {subtask.title}
                            </span>
                            <span className={`rounded-full border px-1.5 py-0.5 text-[10px] ${subtaskStatus.badgeClass}`}>
                              {subtaskStatus.label}
                            </span>
                          </button>

                          {isSubtaskExpanded ? (
                            <div className="ml-5 rounded-xl border border-white/8 bg-white/[0.035] px-3 py-2 text-xs leading-5 text-white/45">
                              <p>{subtask.description}</p>
                              {subtask.tools && subtask.tools.length > 0 ? (
                                <div className="mt-2 flex flex-wrap items-center gap-1.5">
                                  <span className="inline-flex items-center gap-1 font-medium text-white/52">
                                    <Wrench className="h-3 w-3" aria-hidden />
                                    Tools
                                  </span>
                                  {subtask.tools.map((tool) => (
                                    <span
                                      key={tool}
                                      className="rounded-full border border-white/10 bg-white/[0.06] px-1.5 py-0.5 text-[10px] text-white/54"
                                    >
                                      {tool}
                                    </span>
                                  ))}
                                </div>
                              ) : null}
                            </div>
                          ) : null}
                        </li>
                      )
                    })}
                  </ul>
                </div>
              ) : null}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

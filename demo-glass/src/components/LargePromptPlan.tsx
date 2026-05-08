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
import type { PlanPriority, PlanStatus, PromptPlan } from './largePromptPlanData'

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

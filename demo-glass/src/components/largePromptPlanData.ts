export type PlanStatus = 'completed' | 'in-progress' | 'pending' | 'need-help' | 'failed'
export type PlanPriority = 'high' | 'medium' | 'low'

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
      title: goals[0]
        ? toTitle(goals[0], 'Plan the main implementation path')
        : 'Plan the main implementation path',
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

  const tasks = taskTemplates.map((task, taskIndex) => ({
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
  })) satisfies PromptPlan['tasks']

  const titleLine = lines.find((line) => line.length > 10) ?? 'Large prompt plan'

  return {
    title: toTitle(titleLine, 'Large prompt plan'),
    summary: `${prompt.trim().length.toLocaleString()} characters analyzed into ${tasks.length} work streams.`,
    tasks,
  }
}

export const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`
}

export interface AttachedFile {
  id: string
  file: File
  type: string
  preview: string | null
  uploadStatus: string
}

export interface PastedSnippet {
  id: string
  content: string
  timestamp: Date
}

export interface ChatModel {
  id: string
  name: string
  description: string
  badge?: string
}

export interface ChatSendPayload {
  message: string
  files: AttachedFile[]
  pastedContent: PastedSnippet[]
  model: string
  isThinkingEnabled: boolean
}

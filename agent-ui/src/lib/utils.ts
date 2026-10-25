import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export const truncateText = (text: string, limit: number) => {
  if (text) {
    return text.length > limit ? `${text.slice(0, limit)}..` : text
  }
  return ''
}

export const isValidUrl = (url: string): boolean => {
  try {
    const { protocol } = new URL(url.trim())
    return protocol === 'http:' || protocol === 'https:'
  } catch {
    return false
  }
}

export const getJsonMarkdown = (content: object = {}) => {
  let jsonBlock = ''
  try {
    jsonBlock = `\`\`\`json\n${JSON.stringify(content, null, 2)}\n\`\`\``
  } catch {
    jsonBlock = `\`\`\`\n${String(content)}\n\`\`\``
  }

  return jsonBlock
}

import { ReactNode } from 'react'

/**
 * 분석 결과 텍스트에서 **텍스트** 마크다운 볼드를 파싱하여
 * 해당 부분을 볼드체로 렌더링합니다. (텍스트이자 #볼드체)
 */
export function parseInlineBold(text: string): ReactNode[] {
  if (typeof text !== 'string' || !text) return []

  const parts: ReactNode[] = []
  const regex = /\*\*([^*]+)\*\*/g
  let lastIndex = 0
  let match: RegExpExecArray | null

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index))
    }
    parts.push(
      <strong key={`bold-${match.index}`} className="font-bold text-gray-900 dark:text-gray-100">
        {match[1]}
      </strong>
    )
    lastIndex = regex.lastIndex
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex))
  }

  return parts.length > 0 ? parts : [text]
}

interface InlineMarkdownProps {
  children: string
  className?: string
  as?: 'span' | 'p' | 'div'
}

/**
 * 분석 결과 내 텍스트를 렌더링할 때 사용.
 * **텍스트** → 볼드체로 표시, 나머지는 일반 텍스트.
 */
export default function InlineMarkdown({ children, className = '', as: Tag = 'span' }: InlineMarkdownProps) {
  const content = parseInlineBold(children)
  return <Tag className={className}>{content}</Tag>
}

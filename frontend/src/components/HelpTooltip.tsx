import { useState, useEffect } from 'react'

interface HelpTooltipProps {
  content: string
  position?: 'top' | 'bottom' | 'left' | 'right'
}

function HelpTooltip({ content }: HelpTooltipProps) {
  const [isOpen, setIsOpen] = useState(false)

  // ESC 키로 모달 닫기
  useEffect(() => {
    if (isOpen) {
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          setIsOpen(false)
        }
      }
      document.addEventListener('keydown', handleEscape)
      // 모달이 열려있을 때 body 스크롤 방지
      document.body.style.overflow = 'hidden'
      return () => {
        document.removeEventListener('keydown', handleEscape)
        document.body.style.overflow = 'unset'
      }
    }
  }, [isOpen])

  // 내용을 줄바꿈으로 분리
  const contentLines = content.split('\n').filter(line => line.trim())

  return (
    <>
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation()
          setIsOpen(true)
        }}
        className="inline-flex items-center justify-center w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-blue-100/80 dark:bg-blue-900/30 backdrop-blur-sm border border-blue-200/50 dark:border-blue-800/50 hover:bg-blue-200/80 dark:hover:bg-blue-900/40 text-blue-600 dark:text-blue-400 text-xs sm:text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
        aria-label="도움말"
        aria-expanded={isOpen}
      >
        ?
      </button>

      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              setIsOpen(false)
            }
          }}
        >
          {/* 배경 오버레이 */}
          <div className="absolute inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm"></div>

          {/* 모달 */}
          <div className="glass-elevated dark:glass-elevated-dark rounded-2xl shadow-2xl max-w-md w-full max-h-[80vh] relative z-10 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent dark:from-white/5 pointer-events-none"></div>
            <div className="relative z-10 flex flex-col h-full">
              {/* 헤더 */}
              <div className="flex items-center justify-between p-4 sm:p-5 border-b border-gray-200/50 dark:border-gray-700/50">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                  <span className="text-blue-600 dark:text-blue-400">💡</span>
                  도움말
                </h3>
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* 내용 */}
              <div className="flex-1 overflow-y-auto p-4 sm:p-5">
                <div className="space-y-3">
                  {contentLines.map((line, index) => {
                    // 불릿 포인트나 제목 형식 감지
                    const isBullet = line.trim().startsWith('•') || line.trim().startsWith('-')
                    const isTitle = line.trim().endsWith(':') && !isBullet
                    const isBold = line.trim().startsWith('**') && line.trim().endsWith('**')

                    if (isBold) {
                      const text = line.replace(/\*\*/g, '').trim()
                      return (
                        <h4 key={index} className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                          {text}
                        </h4>
                      )
                    }

                    if (isTitle) {
                      return (
                        <h4 key={index} className="text-sm font-semibold text-gray-900 dark:text-gray-100 mt-2">
                          {line.trim()}
                        </h4>
                      )
                    }

                    if (isBullet) {
                      return (
                        <div key={index} className="flex items-start gap-2">
                          <span className="text-blue-600 dark:text-blue-400 mt-1 flex-shrink-0">•</span>
                          <p className="text-xs sm:text-sm text-gray-700 dark:text-gray-300 leading-relaxed flex-1">
                            {line.trim().substring(1).trim()}
                          </p>
                        </div>
                      )
                    }

                    return (
                      <p key={index} className="text-xs sm:text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                        {line.trim()}
                      </p>
                    )
                  })}
                </div>
              </div>

              {/* 푸터 */}
              <div className="p-4 sm:p-5 border-t border-gray-200/50 dark:border-gray-700/50">
                <button
                  onClick={() => setIsOpen(false)}
                  className="w-full px-4 py-2 text-xs sm:text-sm font-medium text-white bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-500 dark:to-purple-500 rounded-lg hover:from-blue-700 hover:to-purple-700 dark:hover:from-blue-600 dark:hover:to-purple-600 transition-all duration-200 shadow-md backdrop-blur-sm relative overflow-hidden"
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent"></div>
                  <span className="relative z-10">확인</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default HelpTooltip

import { useState, useEffect, useRef } from 'react'
import { reportError } from '../services/api'

interface ErrorReportButtonProps {
  analysisId: string
  fieldName: string
  crawlerValue?: any
  reportValue?: any
  onReported?: () => void
}

export default function ErrorReportButton({
  analysisId,
  fieldName,
  crawlerValue,
  reportValue,
  onReported
}: ErrorReportButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [issueType, setIssueType] = useState<'mismatch' | 'missing' | 'incorrect'>('mismatch')
  const [severity, setSeverity] = useState<'high' | 'medium' | 'low'>('medium')
  const [description, setDescription] = useState('')
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const submitTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // 컴포넌트 unmount 시 타이머 정리
  useEffect(() => {
    return () => {
      if (submitTimerRef.current) {
        clearTimeout(submitTimerRef.current)
        submitTimerRef.current = null
      }
    }
  }, [])

  // 모달을 닫는 헬퍼 함수 (타이머 정리 포함)
  const closeModal = () => {
    if (submitTimerRef.current) {
      clearTimeout(submitTimerRef.current)
      submitTimerRef.current = null
    }
    setIsOpen(false)
    setMessage(null)
    setDescription('')
  }

  // ESC 키로 모달 닫기
  useEffect(() => {
    if (isOpen) {
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          if (submitTimerRef.current) {
            clearTimeout(submitTimerRef.current)
            submitTimerRef.current = null
          }
          setIsOpen(false)
          setMessage(null)
          setDescription('')
        }
      }
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setMessage(null)

    try {
      await reportError({
        analysis_id: analysisId,
        field_name: fieldName,
        issue_type: issueType,
        severity: severity,
        user_description: description || undefined,
        crawler_value: crawlerValue,
        report_value: reportValue
      })

      setMessage({ type: 'success', text: '신고가 저장되었습니다.' })
      submitTimerRef.current = setTimeout(() => {
        submitTimerRef.current = null
        setIsOpen(false)
        setDescription('')
        setMessage(null)
        if (onReported) {
          onReported()
        }
      }, 1500)
    } catch (error: any) {
      setMessage({ type: 'error', text: error.message || '신고에 실패했습니다.' })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="px-2 py-1 text-xs font-medium text-red-600 dark:text-red-400 bg-red-50/80 dark:bg-red-900/30 backdrop-blur-sm border border-red-200/50 dark:border-red-800/50 rounded-lg hover:bg-red-100/80 dark:hover:bg-red-900/40 transition-all duration-200"
        title="오류 신고"
      >
        ⚠️ 신고
      </button>

      {isOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) {
              closeModal()
            }
          }}
        >
          {/* 배경 오버레이 */}
          <div className="absolute inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm"></div>
          
          {/* 모달 */}
          <div className="glass-elevated dark:glass-elevated-dark rounded-2xl shadow-2xl max-w-sm w-full relative z-10 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent dark:from-white/5 pointer-events-none"></div>
            <div className="relative z-10 p-5 sm:p-6">
              {/* 헤더 */}
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
                  오류 신고
                </h3>
                <button
                  onClick={closeModal}
                  className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <form onSubmit={handleSubmit} className="space-y-3">
                {/* 필드명 (읽기 전용) */}
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">
                    필드
                  </label>
                  <input
                    type="text"
                    value={fieldName}
                    disabled
                    className="w-full px-3 py-2 text-xs glass-card dark:glass-card-dark border border-gray-200/50 dark:border-gray-700/50 rounded-lg text-gray-500 dark:text-gray-400"
                  />
                </div>

                {/* 문제 유형 */}
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">
                    문제 유형
                  </label>
                  <select
                    value={issueType}
                    onChange={(e) => setIssueType(e.target.value as any)}
                    className="w-full px-3 py-2 text-xs glass-card dark:glass-card-dark border border-gray-200/50 dark:border-gray-700/50 rounded-lg text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                  >
                    <option value="mismatch">불일치</option>
                    <option value="missing">누락</option>
                    <option value="incorrect">잘못된 값</option>
                  </select>
                </div>

                {/* 심각도 */}
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">
                    심각도
                  </label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value as any)}
                    className="w-full px-3 py-2 text-xs glass-card dark:glass-card-dark border border-gray-200/50 dark:border-gray-700/50 rounded-lg text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                  >
                    <option value="high">높음</option>
                    <option value="medium">보통</option>
                    <option value="low">낮음</option>
                  </select>
                </div>

                {/* 설명 (선택사항) */}
                <div>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">
                    설명 <span className="text-gray-400">(선택)</span>
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={2}
                    className="w-full px-3 py-2 text-xs glass-card dark:glass-card-dark border border-gray-200/50 dark:border-gray-700/50 rounded-lg text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none"
                    placeholder="추가 설명을 입력하세요..."
                  />
                </div>

                {/* 메시지 */}
                {message && (
                  <div
                    className={`p-2.5 rounded-lg text-xs ${
                      message.type === 'success'
                        ? 'bg-green-50/80 dark:bg-green-900/30 text-green-700 dark:text-green-300 border border-green-200/50 dark:border-green-800/50'
                        : 'bg-red-50/80 dark:bg-red-900/30 text-red-700 dark:text-red-300 border border-red-200/50 dark:border-red-800/50'
                    }`}
                  >
                    {message.text}
                  </div>
                )}

                {/* 버튼 */}
                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={closeModal}
                    className="flex-1 px-3 py-2 text-xs font-medium text-gray-700 dark:text-gray-300 glass-card dark:glass-card-dark border border-gray-200/50 dark:border-gray-700/50 rounded-lg hover:bg-gray-100/50 dark:hover:bg-gray-800/50 transition-all"
                  >
                    취소
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 px-3 py-2 text-xs font-medium text-white bg-gradient-to-r from-red-600 to-red-500 dark:from-red-500 dark:to-red-400 rounded-lg hover:from-red-700 hover:to-red-600 dark:hover:from-red-600 dark:hover:to-red-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-md backdrop-blur-sm relative overflow-hidden"
                  >
                    <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent"></div>
                    <span className="relative z-10">
                      {isSubmitting ? '신고 중...' : '신고하기'}
                    </span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

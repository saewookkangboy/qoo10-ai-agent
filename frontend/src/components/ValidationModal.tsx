import { useEffect } from 'react'
import { ValidationResult } from '../types'
import ErrorReportButton from './ErrorReportButton'

interface ValidationModalProps {
  validation: ValidationResult
  analysisId?: string
  isOpen: boolean
  onClose: () => void
}

export default function ValidationModal({
  validation,
  analysisId,
  isOpen,
  onClose
}: ValidationModalProps) {
  // ESC 키로 모달 닫기
  useEffect(() => {
    if (isOpen) {
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          onClose()
        }
      }
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  const getSeverityColor = (severity: 'high' | 'medium' | 'low') => {
    switch (severity) {
      case 'high':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
      case 'medium':
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
      case 'low':
        return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900/20 border-gray-200 dark:border-gray-800'
    }
  }

  const getSeverityBadge = (severity: 'high' | 'medium' | 'low') => {
    switch (severity) {
      case 'high':
        return '🔴 높음'
      case 'medium':
        return '🟡 보통'
      case 'low':
        return '⚪ 낮음'
    }
  }

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      {/* 배경 오버레이 */}
      <div className="absolute inset-0 bg-black/40 dark:bg-black/60 backdrop-blur-sm"></div>
      
      {/* 모달 */}
      <div className="glass-elevated dark:glass-elevated-dark rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] relative z-10 overflow-hidden flex flex-col">
        <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent dark:from-white/5 pointer-events-none"></div>
        
        {/* 헤더 */}
        <div className="relative z-10 p-5 sm:p-6 border-b border-gray-200/50 dark:border-gray-700/50">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100 mb-1">
                데이터 검증 결과
              </h3>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                검증 점수: <span className="font-semibold">{validation.validation_score.toFixed(1)}%</span>
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors p-1"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* 스크롤 가능한 컨텐츠 */}
        <div className="relative z-10 flex-1 overflow-y-auto p-5 sm:p-6">
          <div className="space-y-6">
            {/* 불일치 항목 */}
            {validation.mismatches && validation.mismatches.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <h4 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
                    불일치 항목
                  </h4>
                  <span className="px-2.5 py-1 text-xs font-semibold bg-red-600 dark:bg-red-500 text-white rounded-lg">
                    {validation.mismatches.length}개
                  </span>
                </div>
                <div className="space-y-3">
                  {validation.mismatches.map((mismatch, idx) => (
                    <div
                      key={idx}
                      className={`p-4 rounded-lg border ${getSeverityColor(mismatch.severity || 'medium')}`}
                    >
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-semibold text-sm sm:text-base">{mismatch.field}</span>
                            {mismatch.severity && (
                              <span className={`px-2 py-0.5 text-xs rounded-md border ${getSeverityColor(mismatch.severity)}`}>
                                {getSeverityBadge(mismatch.severity)}
                              </span>
                            )}
                          </div>
                          <div className="space-y-1.5 text-xs sm:text-sm">
                            <div className="flex items-start gap-2">
                              <span className="font-medium text-gray-700 dark:text-gray-300 min-w-[80px]">크롤러:</span>
                              <span className="text-gray-600 dark:text-gray-400 break-words">
                                {String(mismatch.crawler_value || '-')}
                              </span>
                            </div>
                            <div className="flex items-start gap-2">
                              <span className="font-medium text-gray-700 dark:text-gray-300 min-w-[80px]">리포트:</span>
                              <span className="text-gray-600 dark:text-gray-400 break-words">
                                {String(mismatch.report_value || '-')}
                              </span>
                            </div>
                          </div>
                        </div>
                        {analysisId && (
                          <div className="flex-shrink-0">
                            <ErrorReportButton
                              analysisId={analysisId}
                              fieldName={mismatch.field}
                              crawlerValue={mismatch.crawler_value}
                              reportValue={mismatch.report_value}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 누락 항목 */}
            {validation.missing_items && validation.missing_items.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <h4 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
                    누락 항목
                  </h4>
                  <span className="px-2.5 py-1 text-xs font-semibold bg-yellow-600 dark:bg-yellow-500 text-white rounded-lg">
                    {validation.missing_items.length}개
                  </span>
                </div>
                <div className="space-y-3">
                  {validation.missing_items.map((missing, idx) => (
                    <div
                      key={idx}
                      className={`p-4 rounded-lg border ${getSeverityColor(missing.severity || 'medium')}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-semibold text-sm sm:text-base">{missing.field}</span>
                            {missing.severity && (
                              <span className={`px-2 py-0.5 text-xs rounded-md border ${getSeverityColor(missing.severity)}`}>
                                {getSeverityBadge(missing.severity)}
                              </span>
                            )}
                          </div>
                          <div className="space-y-1.5 text-xs sm:text-sm">
                            <div className="flex items-start gap-2">
                              <span className="font-medium text-gray-700 dark:text-gray-300 min-w-[120px]">체크리스트 ID:</span>
                              <span className="text-gray-600 dark:text-gray-400 break-words">
                                {missing.checklist_item_id}
                              </span>
                            </div>
                            <div className="flex items-start gap-2">
                              <span className="font-medium text-gray-700 dark:text-gray-300 min-w-[120px]">크롤러 데이터:</span>
                              <span className="text-gray-600 dark:text-gray-400">
                                {missing.crawler_has_data ? '있음' : '없음'}
                              </span>
                            </div>
                          </div>
                        </div>
                        {analysisId && (
                          <div className="flex-shrink-0">
                            <ErrorReportButton
                              analysisId={analysisId}
                              fieldName={missing.field}
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 검증 통과 */}
            {validation.is_valid && (
              <div className="text-center py-8">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 mb-4">
                  <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">
                  모든 검증을 통과했습니다
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  데이터가 일치하고 누락된 항목이 없습니다.
                </p>
              </div>
            )}

            {/* 검증 실패 시 안내 */}
            {!validation.is_valid && validation.mismatches.length === 0 && validation.missing_items.length === 0 && (
              <div className="text-center py-8">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  검증 결과가 없습니다.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* 푸터 */}
        <div className="relative z-10 p-5 sm:p-6 border-t border-gray-200/50 dark:border-gray-700/50">
          <div className="flex items-center justify-between">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              생성일시: {new Date(validation.timestamp).toLocaleString('ko-KR')}
            </p>
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 glass-card dark:glass-card-dark border border-gray-200/50 dark:border-gray-700/50 rounded-lg hover:bg-gray-100/50 dark:hover:bg-gray-800/50 transition-all"
            >
              닫기
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

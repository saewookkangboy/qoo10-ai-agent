import { ChecklistResult } from '../types'
import HelpTooltip from './HelpTooltip'

interface ChecklistCardProps {
  checklist: ChecklistResult
}

const helpContent = '이 체크리스트는 Qoo10 큐텐 대학의 판매 준비 가이드를 기반으로 합니다.\n\n• 상품 등록: 상품명, 설명, 이미지 등 필수 정보를 확인합니다\n• 가격 설정: 판매가, 할인율, 쿠폰 할인 등을 점검합니다\n• 배송 정보: 배송비, 배송 방법, 통관 정보를 확인합니다\n• 프로모션: 샵 쿠폰, 상품 할인, 광고 활용 여부를 점검합니다\n\n완성도가 높을수록 검색 노출과 전환율이 향상됩니다.'

function ChecklistCard({ checklist }: ChecklistCardProps) {
  const overallCompletion = checklist.overall_completion

  const getCompletionColor = (rate: number) => {
    if (rate >= 80) {
      return {
        text: 'text-green-600 dark:text-green-400',
        bg: 'bg-green-50 dark:bg-green-900/20',
        border: 'border-green-500 dark:border-green-400',
        badge: 'bg-green-600 dark:bg-green-500 text-white'
      }
    }
    if (rate >= 60) {
      return {
        text: 'text-yellow-600 dark:text-yellow-400',
        bg: 'bg-yellow-50 dark:bg-yellow-900/20',
        border: 'border-yellow-500 dark:border-yellow-400',
        badge: 'bg-yellow-600 dark:bg-yellow-500 text-white'
      }
    }
    return {
      text: 'text-red-600 dark:text-red-400',
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-500 dark:border-red-400',
      badge: 'bg-red-600 dark:bg-red-500 text-white'
    }
  }

  const overallColors = getCompletionColor(overallCompletion)

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* 전체 완성도 헤더 */}
      <div className={`bg-gradient-to-br ${overallColors.bg} backdrop-blur-xl rounded-2xl shadow-lg border-2 ${overallColors.border} p-4 sm:p-6 glass-transition relative overflow-hidden`}>
        <div className="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent dark:from-white/10 pointer-events-none"></div>
        <div className="relative z-10">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
              📋 메뉴얼 기반 체크리스트
            </h2>
            <HelpTooltip content={helpContent} />
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">전체 완성도</div>
              <div className={`text-3xl sm:text-4xl font-bold ${overallColors.text}`}>{overallCompletion}%</div>
            </div>
            <div className={`px-4 py-2 rounded-lg ${overallColors.badge} font-semibold text-sm sm:text-base shadow-md backdrop-blur-sm`}>
              {overallCompletion >= 80 ? '양호' : overallCompletion >= 60 ? '개선 필요' : '긴급 개선'}
            </div>
          </div>
        </div>
        </div>
      </div>

      {/* 카테고리별 체크리스트 */}
      <div className="space-y-4 sm:space-y-6">
        {checklist.checklists.map((category, idx) => {
          const categoryColors = getCompletionColor(category.completion_rate)
          
          return (
            <div 
              key={idx} 
              className="glass-elevated dark:glass-elevated-dark rounded-2xl p-4 sm:p-6 glass-transition relative overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent dark:from-white/5 pointer-events-none"></div>
              <div className="relative z-10">
                {/* 카테고리 헤더 */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 sm:mb-6 pb-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg sm:text-xl font-semibold text-gray-900 dark:text-gray-100">
                    {category.category}
                  </h3>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-xs text-gray-600 dark:text-gray-400">완성도</div>
                      <div className={`text-xl sm:text-2xl font-bold ${categoryColors.text}`}>
                        {category.completion_rate}%
                      </div>
                    </div>
                    <div className={`px-3 py-1.5 text-xs sm:text-sm font-semibold rounded-lg ${categoryColors.badge} shadow-md backdrop-blur-sm`}>
                      {category.completion_rate >= 80 ? '완료' : category.completion_rate >= 60 ? '진행중' : '미완료'}
                    </div>
                  </div>
                </div>

                {/* 체크리스트 항목 */}
                <div className="space-y-3 sm:space-y-4">
                {category.items.map((item) => {
                  const isCompleted = item.status === 'completed'
                  
                  return (
                    <div
                      key={item.id}
                      className={`border-l-4 rounded-2xl p-4 sm:p-5 glass-transition backdrop-blur-xl relative overflow-hidden ${
                        isCompleted
                          ? 'bg-green-50/80 dark:bg-green-900/30 border-l-green-500 dark:border-l-green-400 border border-green-200/50 dark:border-green-800/50'
                          : 'glass-card dark:glass-card-dark border-l-gray-300 dark:border-l-gray-600 border border-gray-200/50 dark:border-gray-700/50 hover:border-l-gray-400 dark:hover:border-l-gray-500'
                      }`}
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent dark:from-white/5 pointer-events-none"></div>
                      <div className="relative z-10">
                      <div className="flex items-start gap-3 sm:gap-4">
                        {/* 체크 아이콘 */}
                        <div className="flex-shrink-0 mt-0.5">
                          {isCompleted ? (
                            <div className="w-6 h-6 rounded-full bg-green-500 dark:bg-green-400 flex items-center justify-center shadow-md backdrop-blur-sm relative overflow-hidden">
                              <div className="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent"></div>
                              <span className="text-white text-sm font-bold relative z-10">✓</span>
                            </div>
                          ) : (
                            <div className="w-6 h-6 rounded-full border-2 border-gray-300 dark:border-gray-600 glass-card dark:glass-card-dark"></div>
                          )}
                        </div>
                        
                        {/* 내용 */}
                        <div className="flex-1 min-w-0">
                          {/* 제목 및 배지 */}
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            <h4 className={`text-sm sm:text-base font-semibold ${
                              isCompleted 
                                ? 'text-gray-900 dark:text-gray-100' 
                                : 'text-gray-700 dark:text-gray-300'
                            }`}>
                              {item.title}
                            </h4>
                            {item.auto_checked && (
                              <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded border border-blue-200 dark:border-blue-800">
                                자동 체크
                              </span>
                            )}
                          </div>
                          
                          {/* 설명 */}
                          <p className={`text-xs sm:text-sm mb-3 leading-relaxed ${
                            isCompleted
                              ? 'text-gray-600 dark:text-gray-400'
                              : 'text-gray-500 dark:text-gray-500'
                          }`}>
                            {item.description}
                          </p>
                          
                          {/* 추천 사항 */}
                          {item.recommendation && (
                            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                              <div className="flex items-start gap-2">
                                <span className="text-yellow-500 dark:text-yellow-400 text-sm flex-shrink-0 mt-0.5">💡</span>
                                <div className="flex-1">
                                  <p className="text-xs sm:text-sm font-semibold text-yellow-700 dark:text-yellow-300 mb-1">
                                    개선 제안
                                  </p>
                                  <p className="text-xs sm:text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                                    {item.recommendation}
                                  </p>
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                      </div>
                    </div>
                  )
                })}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ChecklistCard

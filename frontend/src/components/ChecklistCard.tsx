import { ChecklistResult } from '../types'
import HelpTooltip from './HelpTooltip'

interface ChecklistCardProps {
  checklist: ChecklistResult
}

const helpContent = '이 체크리스트는 Qoo10 큐텐 대학의 판매 준비 가이드를 기반으로 합니다.\n\n• 상품 등록: 상품명, 설명, 이미지 등 필수 정보를 확인합니다\n• 가격 설정: 판매가, 할인율, 쿠폰 할인 등을 점검합니다\n• 배송 정보: 배송비, 배송 방법, 통관 정보를 확인합니다\n• 프로모션: 샵 쿠폰, 상품 할인, 광고 활용 여부를 점검합니다\n\n완성도가 높을수록 검색 노출과 전환율이 향상됩니다.'

function ChecklistCard({ checklist }: ChecklistCardProps) {
  const overallCompletion = checklist.overall_completion

  const getCompletionColor = (rate: number) => {
    if (rate >= 80) return 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20'
    if (rate >= 60) return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20'
    return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20'
  }

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-4 sm:p-6 transition-colors">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
            📋 메뉴얼 기반 체크리스트
          </h2>
          <HelpTooltip content={helpContent} />
        </div>
        <div className={`px-4 sm:px-6 py-3 sm:py-4 rounded-xl ${getCompletionColor(overallCompletion)} border border-gray-200 dark:border-gray-700`}>
          <div className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400 mb-1">전체 완성도</div>
          <div className="text-2xl sm:text-3xl font-bold">{overallCompletion}%</div>
        </div>
      </div>

      <div className="space-y-4 sm:space-y-6">
        {checklist.checklists.map((category, idx) => (
          <div key={idx} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 sm:p-5 hover:shadow-md transition-all duration-200">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
                {category.category}
              </h3>
              <span className={`px-3 py-1.5 text-xs sm:text-sm font-semibold rounded-lg ${getCompletionColor(category.completion_rate)} border border-gray-200 dark:border-gray-700`}>
                {category.completion_rate}%
              </span>
            </div>

            <div className="space-y-3">
              {category.items.map((item) => (
                <div
                  key={item.id}
                  className={`flex items-start gap-3 p-3 sm:p-4 rounded-lg border ${
                    item.status === 'completed' 
                      ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
                      : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                  }`}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {item.status === 'completed' ? (
                      <span className="text-green-600 dark:text-green-400 text-lg">✅</span>
                    ) : (
                      <span className="text-gray-400 dark:text-gray-600 text-lg">⬜</span>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm sm:text-base font-medium text-gray-900 dark:text-gray-100">
                        {item.title}
                      </span>
                      {item.auto_checked && (
                        <span className="px-2 py-0.5 text-xs font-medium bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded border border-blue-200 dark:border-blue-800">
                          자동 체크
                        </span>
                      )}
                    </div>
                    <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-1">
                      {item.description}
                    </p>
                    {item.recommendation && (
                      <p className="text-xs sm:text-sm text-red-600 dark:text-red-400 mt-2 font-medium">
                        💡 {item.recommendation}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ChecklistCard

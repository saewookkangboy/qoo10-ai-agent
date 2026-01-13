import { ChecklistResult } from '../types'

interface ChecklistCardProps {
  checklist: ChecklistResult
}

function ChecklistCard({ checklist }: ChecklistCardProps) {
  const overallCompletion = checklist.overall_completion

  const getCompletionColor = (rate: number) => {
    if (rate >= 80) return 'text-green-600 bg-green-50'
    if (rate >= 60) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <h2 className="text-xl sm:text-2xl font-bold text-[#1A1A1A]">
          📋 메뉴얼 기반 체크리스트
        </h2>
        <div className={`px-4 sm:px-6 py-2 sm:py-3 rounded-lg ${getCompletionColor(overallCompletion)}`}>
          <div className="text-xs sm:text-sm text-[#4D4D4D] mb-1">전체 완성도</div>
          <div className="text-2xl sm:text-3xl font-bold">{overallCompletion}%</div>
        </div>
      </div>

      <div className="space-y-4 sm:space-y-6">
        {checklist.checklists.map((category, idx) => (
          <div key={idx} className="border border-[#E6E6E6] rounded-lg p-4 sm:p-5">
            <div className="flex items-center justify-between mb-3 sm:mb-4">
              <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A]">
                {category.category}
              </h3>
              <span className={`px-3 py-1 text-xs sm:text-sm font-medium rounded ${getCompletionColor(category.completion_rate)}`}>
                {category.completion_rate}%
              </span>
            </div>

            <div className="space-y-2 sm:space-y-3">
              {category.items.map((item) => (
                <div
                  key={item.id}
                  className={`flex items-start gap-3 p-3 rounded-lg ${
                    item.status === 'completed' ? 'bg-green-50' : 'bg-gray-50'
                  }`}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {item.status === 'completed' ? (
                      <span className="text-green-600 text-lg">✅</span>
                    ) : (
                      <span className="text-gray-400 text-lg">⬜</span>
                    )}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm sm:text-base font-medium text-[#1A1A1A]">
                        {item.title}
                      </span>
                      {item.auto_checked && (
                        <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                          자동 체크
                        </span>
                      )}
                    </div>
                    <p className="text-xs sm:text-sm text-[#4D4D4D] mb-1">
                      {item.description}
                    </p>
                    {item.recommendation && (
                      <p className="text-xs sm:text-sm text-[#CC0000] mt-1">
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

import { Recommendation } from '../types'
import HelpTooltip from './HelpTooltip'

interface RecommendationCardProps {
  recommendation: Recommendation
}

const helpContent = '개선 제안은 Qoo10 큐텐 대학의 판매 노하우를 기반으로 생성되었습니다.\n\n• High Priority: 즉시 개선이 필요한 항목으로 매출에 직접적인 영향을 미칩니다\n• Medium Priority: 단기적으로 개선하면 효과를 볼 수 있는 항목입니다\n• Low Priority: 장기적으로 고려하면 좋은 개선 사항입니다\n\n각 제안의 실행 방법을 따라 단계적으로 개선하시면 매출 증대에 도움이 됩니다.'

function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return {
          border: 'border-l-red-500 dark:border-l-red-400',
          bg: 'bg-red-50 dark:bg-red-900/20',
          badge: 'bg-red-600 dark:bg-red-500 text-white',
          text: 'text-red-600 dark:text-red-400'
        }
      case 'medium':
        return {
          border: 'border-l-yellow-500 dark:border-l-yellow-400',
          bg: 'bg-yellow-50 dark:bg-yellow-900/20',
          badge: 'bg-yellow-600 dark:bg-yellow-500 text-white',
          text: 'text-yellow-600 dark:text-yellow-400'
        }
      case 'low':
        return {
          border: 'border-l-blue-500 dark:border-l-blue-400',
          bg: 'bg-blue-50 dark:bg-blue-900/20',
          badge: 'bg-blue-600 dark:bg-blue-500 text-white',
          text: 'text-blue-600 dark:text-blue-400'
        }
      default:
        return {
          border: 'border-l-gray-500 dark:border-l-gray-400',
          bg: 'bg-gray-50 dark:bg-gray-800',
          badge: 'bg-gray-600 dark:bg-gray-500 text-white',
          text: 'text-gray-600 dark:text-gray-400'
        }
    }
  }

  const colors = getPriorityColor(recommendation.priority)

  return (
    <div className={`border-l-4 rounded-2xl p-4 sm:p-5 ${colors.border} backdrop-blur-xl ${colors.bg} glass-transition border border-gray-200/50 dark:border-gray-700/50 relative overflow-hidden`}>
      <div className="absolute inset-0 bg-gradient-to-r from-white/20 to-transparent dark:from-white/5 pointer-events-none"></div>
      <div className="relative z-10">
      {/* 헤더 */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-3 sm:mb-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
              {recommendation.title}
            </h3>
            <HelpTooltip content={helpContent} />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-block px-2 sm:px-3 py-1 text-xs font-medium rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700">
              {recommendation.category}
            </span>
            <span className={`px-2 sm:px-3 py-1 text-xs font-medium rounded ${colors.badge}`}>
              {recommendation.priority === 'high' ? '높음' :
               recommendation.priority === 'medium' ? '중간' : '낮음'}
            </span>
          </div>
        </div>
      </div>
      
      {/* 설명 */}
      <p className="text-sm sm:text-base text-gray-900 dark:text-gray-100 mb-4 sm:mb-5 leading-relaxed">
        {recommendation.description}
      </p>
      
      {/* 실행 방법 */}
      {recommendation.action_items && recommendation.action_items.length > 0 && (
        <div className="mb-4 sm:mb-5 glass-card dark:glass-card-dark rounded-xl p-3 sm:p-4 border border-gray-200/50 dark:border-gray-700/50">
          <p className="text-xs sm:text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2 sm:mb-3">실행 방법</p>
          <ul className="space-y-1.5 sm:space-y-2">
            {recommendation.action_items.map((item, idx) => (
              <li key={idx} className="text-xs sm:text-sm text-gray-900 dark:text-gray-100 flex items-start">
                <span className="text-blue-600 dark:text-blue-400 mr-2 mt-0.5 flex-shrink-0">✓</span>
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* 메타 정보 */}
      <div className="flex flex-wrap items-center gap-3 sm:gap-4 pt-3 sm:pt-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-600 dark:text-gray-400">예상 효과:</span>
          <span className="text-xs font-medium text-gray-900 dark:text-gray-100">{recommendation.expected_impact}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-600 dark:text-gray-400">난이도:</span>
          <span className="text-xs font-medium text-gray-900 dark:text-gray-100">{recommendation.difficulty}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-gray-600 dark:text-gray-400">예상 시간:</span>
          <span className="text-xs font-medium text-gray-900 dark:text-gray-100">{recommendation.estimated_time}</span>
        </div>
      </div>
      </div>
    </div>
  )
}

export default RecommendationCard

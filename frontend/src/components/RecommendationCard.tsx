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
    <div className={`border-l-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800/80 p-4 ${colors.border} ${colors.bg}`}>
      <div className="flex items-start gap-2 mb-2">
        <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 flex-1">
          {recommendation.title}
        </h3>
        <HelpTooltip content={helpContent} />
      </div>
      <div className="flex flex-wrap gap-2 mb-3">
        <span className="px-2 py-0.5 text-xs font-medium rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
          {recommendation.category}
        </span>
        <span className={`px-2 py-0.5 text-xs font-medium rounded ${colors.badge}`}>
          {recommendation.priority === 'high' ? '높음' : recommendation.priority === 'medium' ? '중간' : '낮음'}
        </span>
      </div>
      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
        {recommendation.description}
      </p>
      {recommendation.action_items && recommendation.action_items.length > 0 && (
        <div className="rounded-lg border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 p-3 mb-4">
          <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">실행 방법</p>
          <ul className="space-y-1">
            {recommendation.action_items.map((item, idx) => (
              <li key={idx} className="text-xs text-gray-700 dark:text-gray-300 flex gap-2">
                <span className="text-blue-500 flex-shrink-0">✓</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      <div className="flex flex-wrap gap-x-4 gap-y-1 pt-3 border-t border-gray-100 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
        <span>효과: <span className="font-medium text-gray-700 dark:text-gray-300">{recommendation.expected_impact}</span></span>
        <span>난이도: <span className="font-medium text-gray-700 dark:text-gray-300">{recommendation.difficulty}</span></span>
        <span>예상: <span className="font-medium text-gray-700 dark:text-gray-300">{recommendation.estimated_time}</span></span>
      </div>
    </div>
  )
}

export default RecommendationCard

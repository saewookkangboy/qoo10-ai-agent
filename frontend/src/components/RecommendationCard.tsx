import { Recommendation } from '../types'

interface RecommendationCardProps {
  recommendation: Recommendation
}

function RecommendationCard({ recommendation }: RecommendationCardProps) {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return {
          border: 'border-l-[#CC0000]',
          bg: 'bg-red-50',
          badge: 'bg-[#CC0000] text-white',
          text: 'text-[#CC0000]'
        }
      case 'medium':
        return {
          border: 'border-l-[#FF9900]',
          bg: 'bg-yellow-50',
          badge: 'bg-[#FF9900] text-white',
          text: 'text-[#FF9900]'
        }
      case 'low':
        return {
          border: 'border-l-[#0066CC]',
          bg: 'bg-blue-50',
          badge: 'bg-[#0066CC] text-white',
          text: 'text-[#0066CC]'
        }
      default:
        return {
          border: 'border-l-[#808080]',
          bg: 'bg-gray-50',
          badge: 'bg-[#808080] text-white',
          text: 'text-[#808080]'
        }
    }
  }

  const colors = getPriorityColor(recommendation.priority)

  return (
    <div className={`border-l-4 rounded-lg p-4 sm:p-5 ${colors.border} ${colors.bg} hover:shadow-[0_2px_4px_rgba(0,0,0,0.08)] transition-shadow duration-200`}>
      {/* 헤더 */}
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-3 sm:mb-4">
        <div className="flex-1">
          <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A] mb-2">
            {recommendation.title}
          </h3>
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-block px-2 sm:px-3 py-1 text-xs font-medium rounded bg-white text-[#4D4D4D] border border-[#E6E6E6]">
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
      <p className="text-sm sm:text-base text-[#1A1A1A] mb-4 sm:mb-5 leading-relaxed">
        {recommendation.description}
      </p>
      
      {/* 실행 방법 */}
      {recommendation.action_items && recommendation.action_items.length > 0 && (
        <div className="mb-4 sm:mb-5 bg-white rounded-lg p-3 sm:p-4">
          <p className="text-xs sm:text-sm font-semibold text-[#1A1A1A] mb-2 sm:mb-3">실행 방법</p>
          <ul className="space-y-1.5 sm:space-y-2">
            {recommendation.action_items.map((item, idx) => (
              <li key={idx} className="text-xs sm:text-sm text-[#1A1A1A] flex items-start">
                <span className="text-[#0066CC] mr-2 mt-0.5 flex-shrink-0">✓</span>
                <span className="leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {/* 메타 정보 */}
      <div className="flex flex-wrap items-center gap-3 sm:gap-4 pt-3 sm:pt-4 border-t border-white/50">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-[#4D4D4D]">예상 효과:</span>
          <span className="text-xs font-medium text-[#1A1A1A]">{recommendation.expected_impact}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-[#4D4D4D]">난이도:</span>
          <span className="text-xs font-medium text-[#1A1A1A]">{recommendation.difficulty}</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-[#4D4D4D]">예상 시간:</span>
          <span className="text-xs font-medium text-[#1A1A1A]">{recommendation.estimated_time}</span>
        </div>
      </div>
    </div>
  )
}

export default RecommendationCard

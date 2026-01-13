interface ScoreCardProps {
  title: string
  score: number
  analysis: any
}

function ScoreCard({ title, score, analysis }: ScoreCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return {
      bg: 'bg-[#00AA44]',
      text: 'text-[#00AA44]',
      bgLight: 'bg-green-50',
      border: 'border-[#00AA44]'
    }
    if (score >= 60) return {
      bg: 'bg-[#FF9900]',
      text: 'text-[#FF9900]',
      bgLight: 'bg-yellow-50',
      border: 'border-[#FF9900]'
    }
    return {
      bg: 'bg-[#CC0000]',
      text: 'text-[#CC0000]',
      bgLight: 'bg-red-50',
      border: 'border-[#CC0000]'
    }
  }

  const getScoreLabel = (score: number) => {
    if (score >= 80) return '양호'
    if (score >= 60) return '개선 필요'
    return '긴급 개선'
  }

  const colors = getScoreColor(score)

  return (
    <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6 hover:shadow-[0_4px_8px_rgba(0,0,0,0.12)] transition-shadow duration-200">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A]">{title}</h3>
        <span className={`px-2 sm:px-3 py-1 text-xs sm:text-sm font-medium rounded ${colors.bgLight} ${colors.text}`}>
          {getScoreLabel(score)}
        </span>
      </div>

      {/* 점수 표시 영역 */}
      <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 mb-4 sm:mb-6">
        {/* 큰 점수 원형 표시 */}
        <div className={`w-20 h-20 sm:w-24 sm:h-24 rounded-full ${colors.bg} flex items-center justify-center text-white font-bold text-2xl sm:text-3xl flex-shrink-0`}>
          {score}
        </div>
        
        {/* 진행 바 및 세부 정보 */}
        <div className="flex-1 w-full sm:w-auto">
          <div className="w-full bg-[#E6E6E6] rounded-full h-2 sm:h-2.5 mb-3">
            <div
              className={`h-full rounded-full ${colors.bg} transition-all duration-500`}
              style={{ width: `${score}%` }}
            ></div>
          </div>
          <div className="text-xs sm:text-sm text-[#4D4D4D]">
            <span className="font-medium">{score}점</span>
            <span className="mx-1">/</span>
            <span>100점</span>
          </div>
        </div>
      </div>

      {/* 주요 제안 */}
      {analysis.recommendations && analysis.recommendations.length > 0 && (
        <div className="mt-4 sm:mt-6 pt-4 sm:pt-6 border-t border-[#E6E6E6]">
          <p className="text-xs sm:text-sm font-medium text-[#4D4D4D] mb-2 sm:mb-3">주요 제안</p>
          <ul className="space-y-1.5 sm:space-y-2">
            {analysis.recommendations.slice(0, 2).map((rec: string, idx: number) => (
              <li key={idx} className="flex items-start text-xs sm:text-sm text-[#1A1A1A]">
                <span className="text-[#0066CC] mr-2 mt-0.5 flex-shrink-0">•</span>
                <span className="leading-relaxed">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default ScoreCard

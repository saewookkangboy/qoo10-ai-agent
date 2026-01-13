interface AIInsightReportProps {
  report: {
    period_days: number
    statistics: {
      score: any
      analysis: any
    }
    insights: Array<{
      type: 'warning' | 'success' | 'info'
      title: string
      description: string
      recommendation: string
    }>
    generated_at: string
  }
}

function AIInsightReport({ report }: AIInsightReportProps) {
  const getInsightColor = (type: string) => {
    switch (type) {
      case 'warning':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800'
      case 'success':
        return 'bg-green-50 border-green-200 text-green-800'
      case 'info':
        return 'bg-blue-50 border-blue-200 text-blue-800'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800'
    }
  }

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'warning':
        return '⚠️'
      case 'success':
        return '✅'
      case 'info':
        return 'ℹ️'
      default:
        return '📌'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <h2 className="text-xl sm:text-2xl font-bold text-[#1A1A1A]">🤖 AI 분석 리포트</h2>
        <span className="text-xs sm:text-sm text-[#4D4D4D]">
          최근 {report.period_days}일 기준
        </span>
      </div>

      {report.insights.length === 0 ? (
        <div className="text-center py-8 text-[#4D4D4D]">
          인사이트가 없습니다.
        </div>
      ) : (
        <div className="space-y-4">
          {report.insights.map((insight, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-lg border ${getInsightColor(insight.type)}`}
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{getInsightIcon(insight.type)}</span>
                <div className="flex-1">
                  <h3 className="font-semibold text-base sm:text-lg mb-2">
                    {insight.title}
                  </h3>
                  <p className="text-sm sm:text-base mb-2 opacity-90">
                    {insight.description}
                  </p>
                  <p className="text-xs sm:text-sm font-medium opacity-75">
                    💡 {insight.recommendation}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-4 pt-4 border-t border-[#E6E6E6] text-xs text-[#4D4D4D] text-center">
        생성일시: {new Date(report.generated_at).toLocaleString('ko-KR')}
      </div>
    </div>
  )
}

export default AIInsightReport

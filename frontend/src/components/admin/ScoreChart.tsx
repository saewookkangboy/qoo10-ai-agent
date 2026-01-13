interface ScoreChartProps {
  data: {
    overall: {
      avg_score: number
      max_score: number
      min_score: number
      total_count: number
      excellent_count: number
      good_count: number
      poor_count: number
    }
    daily: Array<{
      date: string
      avg_score: number
      count: number
    }>
  }
}

function ScoreChart({ data }: ScoreChartProps) {
  const { overall, daily } = data

  // 간단한 막대 그래프 (CSS만 사용)
  const maxScore = 100
  const avgScore = overall.avg_score || 0
  const maxBarScore = overall.max_score || 0
  const minBarScore = overall.min_score || 0

  return (
    <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6">
      <h2 className="text-xl sm:text-2xl font-bold text-[#1A1A1A] mb-4 sm:mb-6">
        📈 점수 통계
      </h2>

      {/* 전체 통계 카드 */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-4 bg-blue-50 rounded-lg">
          <div className="text-2xl sm:text-3xl font-bold text-blue-700">{Math.round(avgScore)}</div>
          <div className="text-xs sm:text-sm text-[#4D4D4D] mt-1">평균 점수</div>
        </div>
        <div className="text-center p-4 bg-green-50 rounded-lg">
          <div className="text-2xl sm:text-3xl font-bold text-green-700">{maxBarScore}</div>
          <div className="text-xs sm:text-sm text-[#4D4D4D] mt-1">최대 점수</div>
        </div>
        <div className="text-center p-4 bg-yellow-50 rounded-lg">
          <div className="text-2xl sm:text-3xl font-bold text-yellow-700">{minBarScore}</div>
          <div className="text-xs sm:text-sm text-[#4D4D4D] mt-1">최소 점수</div>
        </div>
        <div className="text-center p-4 bg-purple-50 rounded-lg">
          <div className="text-2xl sm:text-3xl font-bold text-purple-700">{overall.total_count || 0}</div>
          <div className="text-xs sm:text-sm text-[#4D4D4D] mt-1">총 분석 수</div>
        </div>
      </div>

      {/* 점수 분포 */}
      <div className="mb-6">
        <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A] mb-3">점수 분포</h3>
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-green-700 font-medium">우수 (80점 이상)</span>
              <span>{overall.excellent_count || 0}개</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-green-500 h-3 rounded-full transition-all"
                style={{
                  width: `${((overall.excellent_count || 0) / (overall.total_count || 1)) * 100}%`
                }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-yellow-700 font-medium">양호 (60-79점)</span>
              <span>{overall.good_count || 0}개</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-yellow-500 h-3 rounded-full transition-all"
                style={{
                  width: `${((overall.good_count || 0) / (overall.total_count || 1)) * 100}%`
                }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-red-700 font-medium">개선 필요 (60점 미만)</span>
              <span>{overall.poor_count || 0}개</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-red-500 h-3 rounded-full transition-all"
                style={{
                  width: `${((overall.poor_count || 0) / (overall.total_count || 1)) * 100}%`
                }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 일별 추이 (간단한 막대 그래프) */}
      {daily && daily.length > 0 && (
        <div>
          <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A] mb-3">일별 평균 점수 추이</h3>
          <div className="flex items-end gap-2 h-48 overflow-x-auto pb-4">
            {daily.slice(-14).map((day, idx) => (
              <div key={idx} className="flex flex-col items-center flex-shrink-0" style={{ minWidth: '40px' }}>
                <div
                  className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                  style={{
                    height: `${(day.avg_score / maxScore) * 180}px`,
                    minHeight: '4px'
                  }}
                  title={`${day.date}: ${Math.round(day.avg_score)}점`}
                />
                <div className="text-xs text-[#4D4D4D] mt-2 text-center">
                  {new Date(day.date).getDate()}일
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default ScoreChart

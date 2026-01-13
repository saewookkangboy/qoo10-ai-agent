import { useNavigate } from 'react-router-dom'

interface AnalysisResultsListProps {
  results: {
    results: Array<{
      analysis_id: string
      url: string
      url_type: string
      overall_score: number
      created_at: string
    }>
    total: number
  }
}

function AnalysisResultsList({ results }: AnalysisResultsListProps) {
  const navigate = useNavigate()

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'bg-green-100 text-green-700 border-green-300'
    if (score >= 60) return 'bg-yellow-100 text-yellow-700 border-yellow-300'
    return 'bg-red-100 text-red-700 border-red-300'
  }

  const handleResultClick = (analysisId: string) => {
    navigate(`/analysis/${analysisId}`)
  }

  return (
    <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <h2 className="text-xl sm:text-2xl font-bold text-[#1A1A1A]">📋 분석 결과 리스트</h2>
        <span className="px-3 py-1 text-xs sm:text-sm bg-gray-100 text-[#4D4D4D] rounded-full">
          총 {results.total}개
        </span>
      </div>

      <div className="space-y-3">
        {results.results.length === 0 ? (
          <div className="text-center py-8 text-[#4D4D4D]">
            분석 결과가 없습니다.
          </div>
        ) : (
          results.results.map((result) => (
            <div
              key={result.analysis_id}
              onClick={() => handleResultClick(result.analysis_id)}
              className="p-4 border border-[#E6E6E6] rounded-lg hover:bg-gray-50 hover:border-[#0066CC] cursor-pointer transition-all"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-[#1A1A1A] truncate mb-1">
                    {result.url}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-[#4D4D4D]">
                    <span>{result.url_type}</span>
                    <span>•</span>
                    <span>{formatDate(result.created_at)}</span>
                  </div>
                </div>
                <div className={`ml-4 px-4 py-2 rounded-lg border font-bold ${getScoreColor(result.overall_score)}`}>
                  {result.overall_score}점
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default AnalysisResultsList

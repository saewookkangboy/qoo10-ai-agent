interface LogViewerProps {
  title: string
  logs: any[]
  total: number
  type: 'analysis' | 'error' | 'user'
}

function LogViewer({ title, logs, total, type }: LogViewerProps) {
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

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'text-gray-500'
    if (score >= 80) return 'text-green-600'
    if (score >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <h2 className="text-xl sm:text-2xl font-bold text-[#1A1A1A]">{title}</h2>
        <span className="px-3 py-1 text-xs sm:text-sm bg-gray-100 text-[#4D4D4D] rounded-full">
          총 {total}개
        </span>
      </div>

      <div className="space-y-3 max-h-96 overflow-y-auto">
        {logs.length === 0 ? (
          <div className="text-center py-8 text-[#4D4D4D]">
            로그가 없습니다.
          </div>
        ) : (
          logs.map((log, idx) => (
            <div
              key={idx}
              className="p-3 sm:p-4 border border-[#E6E6E6] rounded-lg hover:bg-gray-50 transition-colors"
            >
              {type === 'analysis' && (
                <>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-[#1A1A1A] truncate">
                        {log.url}
                      </div>
                      <div className="text-xs text-[#4D4D4D] mt-1">
                        {log.url_type} • {formatDate(log.created_at)}
                      </div>
                    </div>
                    {log.overall_score !== null && (
                      <div className={`ml-3 text-lg font-bold ${getScoreColor(log.overall_score)}`}>
                        {log.overall_score}점
                      </div>
                    )}
                  </div>
                  {log.analysis_id && (
                    <div className="text-xs text-[#0066CC] mt-2">
                      ID: {log.analysis_id.substring(0, 8)}...
                    </div>
                  )}
                </>
              )}

              {type === 'error' && (
                <>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-[#CC0000] truncate">
                        {log.url || 'Unknown URL'}
                      </div>
                      <div className="text-xs text-[#4D4D4D] mt-1">
                        {formatDate(log.crawled_at)}
                      </div>
                    </div>
                    {log.status_code && (
                      <div className="ml-3 px-2 py-1 text-xs bg-red-100 text-red-700 rounded">
                        {log.status_code}
                      </div>
                    )}
                  </div>
                  {log.error_message && (
                    <div className="text-xs text-[#4D4D4D] mt-2 p-2 bg-red-50 rounded">
                      {log.error_message}
                    </div>
                  )}
                </>
              )}

              {type === 'user' && (
                <>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-[#1A1A1A] truncate">
                        {log.url}
                      </div>
                      <div className="text-xs text-[#4D4D4D] mt-1">
                        분석 {log.analysis_count}회 • 마지막 분석: {formatDate(log.last_analyzed)}
                      </div>
                    </div>
                    {log.avg_score !== null && (
                      <div className={`ml-3 text-lg font-bold ${getScoreColor(log.avg_score)}`}>
                        {Math.round(log.avg_score)}점
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default LogViewer

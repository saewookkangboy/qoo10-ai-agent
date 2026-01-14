import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { analyzeService } from '../services/api'
import URLInput from '../components/URLInput'
import LoadingSpinner from '../components/LoadingSpinner'
import ManualSearch from '../components/ManualSearch'
import ThemeToggle from '../components/ThemeToggle'

function HomePage() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showManual, setShowManual] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const response = await analyzeService.startAnalysis({ url })
      navigate(`/analysis/${response.analysis_id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || '분석 시작에 실패했습니다.')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-50 dark:from-gray-950 dark:to-gray-900 transition-colors">
      {/* 헤더 */}
      <div className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 px-4 sm:px-6 py-3 sm:py-4 transition-colors">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-gray-100">Qoo10 Sales Intelligence Agent</h1>
          <div className="flex items-center gap-4">
            <ThemeToggle />
            <Link
              to="/admin"
              className="text-sm sm:text-base text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
            >
              관리자
            </Link>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <div className="max-w-2xl w-full">
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-lg border border-gray-200 dark:border-gray-800 p-6 sm:p-8 lg:p-10 transition-colors">
            {/* 헤더 */}
            <div className="text-center mb-6 sm:mb-8">
            <div className="mb-4 sm:mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 bg-blue-600 dark:bg-blue-500 rounded-full mb-3 sm:mb-4">
                <span className="text-2xl sm:text-3xl">📊</span>
              </div>
            </div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2 sm:mb-3">
              Qoo10 Sales Intelligence Agent
            </h1>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 leading-relaxed">
              Qoo10 Japan 입점 브랜드를 위한 AI 기반 커머스 분석 플랫폼
            </p>
          </div>

          {/* URL 입력 */}
          <URLInput
            url={url}
            onChange={setUrl}
            onSubmit={handleSubmit}
            loading={loading}
            error={error}
          />

          {/* 로딩 상태 */}
          {loading && (
            <div className="mt-6 sm:mt-8 flex flex-col items-center justify-center">
              <LoadingSpinner />
              <p className="mt-4 text-sm sm:text-base text-gray-600 dark:text-gray-400">분석 중입니다...</p>
            </div>
          )}

          {/* 안내 텍스트 */}
          <div className="mt-6 sm:mt-8 pt-6 sm:pt-8 border-t border-gray-200 dark:border-gray-700">
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 sm:p-5 border border-blue-200 dark:border-blue-800">
              <div className="flex items-start gap-3">
                <span className="text-lg sm:text-xl flex-shrink-0">💡</span>
                <div className="flex-1">
                  <p className="text-xs sm:text-sm font-medium text-gray-900 dark:text-gray-100 mb-1 sm:mb-2">
                    사용 방법
                  </p>
                  <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 leading-relaxed mb-2">
                    Qoo10 상품 또는 Shop URL을 입력하면 자동으로 분석합니다.
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 font-mono break-all mb-3">
                    예: https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=...
                  </p>
                  <button
                    onClick={() => setShowManual(!showManual)}
                    className="text-xs sm:text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium underline transition-colors"
                  >
                    📚 Qoo10 큐텐 대학 메뉴얼 검색 {showManual ? '▲' : '▼'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* 메뉴얼 검색 섹션 */}
          {showManual && (
            <div className="mt-4 sm:mt-6">
              <ManualSearch onClose={() => setShowManual(false)} />
            </div>
          )}
        </div>
      </div>
    </div>
    </div>
  )
}

export default HomePage

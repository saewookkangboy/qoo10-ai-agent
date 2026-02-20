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
      // 에러 메시지 추출 (다양한 형식 지원)
      const errorMessage = err.message || err.response?.data?.detail || err.response?.data?.message || '분석 시작에 실패했습니다.'
      setError(errorMessage)
      setLoading(false)
      console.error('Analysis start error:', err)
    }
  }

  return (
    <div className="min-h-screen glass-bg dark:glass-bg-dark transition-colors relative overflow-hidden">
      {/* 배경 장식 요소 */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-400/10 dark:bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-400/10 dark:bg-purple-500/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-pink-400/10 dark:bg-pink-500/10 rounded-full blur-3xl"></div>
      </div>
      
      {/* 헤더 */}
      <div className="glass-elevated dark:glass-elevated-dark border-b border-gray-200/50 dark:border-gray-800/50 px-4 sm:px-6 py-3 sm:py-4 relative z-20">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <h1 className="text-lg sm:text-xl font-bold text-gray-900 dark:text-gray-100">SIA with Qoo10</h1>
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

      <div className="flex items-center justify-center px-4 sm:px-6 lg:px-8 py-8 sm:py-12 relative z-10">
        <div className="max-w-2xl w-full">
          <div className="glass-elevated dark:glass-elevated-dark rounded-2xl p-6 sm:p-8 lg:p-10 glass-transition relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent dark:from-white/5 pointer-events-none"></div>
            <div className="relative z-10">
              {/* 헤더 */}
              <div className="text-center mb-6 sm:mb-8">
                <h2 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2 sm:mb-3">
                  Qoo10 Sales Intelligence Agent
                </h2>
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
              <div className="mt-6 sm:mt-8 pt-6 sm:pt-8 border-t border-gray-200/50 dark:border-gray-700/50">
                <div className="bg-blue-50/80 dark:bg-blue-900/30 backdrop-blur-xl rounded-xl p-4 sm:p-5 border border-blue-200/50 dark:border-blue-800/50 shadow-md relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent pointer-events-none"></div>
                  <div className="relative z-10">
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
    </div>
  )
}

export default HomePage

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeService } from '../services/api'
import URLInput from '../components/URLInput'
import LoadingSpinner from '../components/LoadingSpinner'

function HomePage() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#E6F2FF] to-[#F5F5F5] px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
      <div className="max-w-2xl w-full">
        <div className="bg-white rounded-lg shadow-[0_8px_24px_rgba(0,0,0,0.16)] p-6 sm:p-8 lg:p-10">
          {/* 헤더 */}
          <div className="text-center mb-6 sm:mb-8">
            <div className="mb-4 sm:mb-6">
              <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 bg-[#0066CC] rounded-full mb-3 sm:mb-4">
                <span className="text-2xl sm:text-3xl">📊</span>
              </div>
            </div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-[#1A1A1A] mb-2 sm:mb-3">
              Qoo10 Sales Intelligence Agent
            </h1>
            <p className="text-sm sm:text-base text-[#4D4D4D] leading-relaxed">
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
              <p className="mt-4 text-sm sm:text-base text-[#4D4D4D]">분석 중입니다...</p>
            </div>
          )}

          {/* 안내 텍스트 */}
          <div className="mt-6 sm:mt-8 pt-6 sm:pt-8 border-t border-[#E6E6E6]">
            <div className="bg-[#E6F2FF] rounded-lg p-4 sm:p-5">
              <div className="flex items-start gap-3">
                <span className="text-lg sm:text-xl flex-shrink-0">💡</span>
                <div className="flex-1">
                  <p className="text-xs sm:text-sm font-medium text-[#1A1A1A] mb-1 sm:mb-2">
                    사용 방법
                  </p>
                  <p className="text-xs sm:text-sm text-[#4D4D4D] leading-relaxed mb-2">
                    Qoo10 상품 또는 Shop URL을 입력하면 자동으로 분석합니다.
                  </p>
                  <p className="text-xs text-[#808080] font-mono break-all">
                    예: https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=...
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default HomePage

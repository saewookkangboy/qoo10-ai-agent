import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { analyzeService } from '../services/api'
import { AnalysisResult } from '../types'
import AnalysisReport from '../components/AnalysisReport'
import LoadingSpinner from '../components/LoadingSpinner'

function AnalysisPage() {
  const { analysisId } = useParams<{ analysisId: string }>()
  const navigate = useNavigate()
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!analysisId) return

    const fetchResult = async () => {
      try {
        const analysisResult = await analyzeService.pollAnalysisResult(
          analysisId,
          (updatedResult) => {
            setResult(updatedResult)
            if (updatedResult.status === 'completed' || updatedResult.status === 'failed') {
              setLoading(false)
            }
          }
        )
        setResult(analysisResult)
        setLoading(false)
      } catch (err: any) {
        setError(err.message || '분석 결과를 가져오는데 실패했습니다.')
        setLoading(false)
      }
    }

    fetchResult()
  }, [analysisId])

  if (loading) {
    const progress = result?.progress
    const stageMessages: Record<string, string> = {
      "initializing": "분석을 초기화하는 중...",
      "crawling": "상품 페이지를 수집하는 중...",
      "analyzing": "상품 데이터를 분석하는 중...",
      "generating_recommendations": "개선 제안을 생성하는 중...",
      "evaluating_checklist": "체크리스트를 평가하는 중...",
      "finalizing": "결과를 정리하는 중..."
    }
    
    const message = progress?.message || stageMessages[progress?.stage || ""] || "분석 중입니다..."
    const percentage = progress?.percentage || 0
    
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F5F5F5] px-4">
        <div className="text-center max-w-md w-full">
          <LoadingSpinner />
          <p className="mt-6 text-base sm:text-lg text-[#1A1A1A] font-medium mb-2">
            {message}
          </p>
          {percentage > 0 && (
            <div className="mt-4 mb-2">
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-[#0066CC] h-2.5 rounded-full transition-all duration-300"
                  style={{ width: `${percentage}%` }}
                ></div>
              </div>
              <p className="mt-2 text-xs text-[#4D4D4D]">{percentage}%</p>
            </div>
          )}
          <p className="text-sm sm:text-base text-[#4D4D4D]">
            잠시만 기다려주세요
          </p>
        </div>
      </div>
    )
  }

  if (error || (result && result.status === 'failed')) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F5F5F5] px-4">
        <div className="text-center max-w-md w-full bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-6 sm:p-8">
          <div className="mb-4">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-red-50 rounded-full">
              <span className="text-3xl">⚠️</span>
            </div>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-[#1A1A1A] mb-3">
            분석 실패
          </h2>
          <p className="text-sm sm:text-base text-[#CC0000] mb-6">
            {error || result?.error || '분석에 실패했습니다.'}
          </p>
          <button
            onClick={() => window.location.href = '/'}
            className="px-6 py-3 bg-[#0066CC] text-white rounded-lg font-medium hover:bg-[#004499] transition-colors"
          >
            다시 시도
          </button>
        </div>
      </div>
    )
  }

  if (result && result.status === 'completed' && result.result) {
    return (
      <div>
        <div className="bg-white border-b border-[#E6E6E6] px-4 sm:px-6 py-3 sm:py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="text-sm sm:text-base text-[#0066CC] hover:text-[#004499] font-medium"
            >
              ← 새로운 분석
            </button>
          </div>
        </div>
        <AnalysisReport result={result.result} analysisId={analysisId} />
      </div>
    )
  }

  return null
}

export default AnalysisPage

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
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900/50 px-4">
        <div className="text-center max-w-md w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800/80 p-8">
          <LoadingSpinner />
          <p className="mt-6 text-base text-gray-900 dark:text-gray-100 font-medium">{message}</p>
          {percentage > 0 && (
            <div className="mt-4">
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div className="bg-blue-500 dark:bg-blue-400 h-2 rounded-full transition-all duration-300" style={{ width: `${percentage}%` }} />
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{percentage}%</p>
            </div>
          )}
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">잠시만 기다려주세요</p>
        </div>
      </div>
    )
  }

  if (error || (result && result.status === 'failed')) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900/50 px-4">
        <div className="text-center max-w-md w-full rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800/80 p-8">
          <div className="mb-4 inline-flex items-center justify-center w-14 h-14 rounded-full bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800">
            <span className="text-2xl">⚠️</span>
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">분석 실패</h2>
          <p className="text-sm text-red-600 dark:text-red-400 mb-6">{error || result?.error || '분석에 실패했습니다.'}</p>
          <button
            onClick={() => navigate('/')}
            className="px-5 py-2.5 bg-blue-600 dark:bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors"
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
        <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800/80 px-4 sm:px-6 py-3">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="text-sm text-blue-600 dark:text-blue-400 hover:underline font-medium"
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

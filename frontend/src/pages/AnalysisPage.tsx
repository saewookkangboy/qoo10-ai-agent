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
      <div className="min-h-screen flex items-center justify-center glass-bg dark:glass-bg-dark px-4 transition-colors relative overflow-hidden">
        {/* 배경 장식 요소 */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-400/10 dark:bg-blue-500/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-400/10 dark:bg-purple-500/10 rounded-full blur-3xl"></div>
        </div>
        
        <div className="text-center max-w-md w-full relative z-10">
          <div className="glass-elevated dark:glass-elevated-dark rounded-2xl p-8 sm:p-10 glass-transition relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent dark:from-white/5 pointer-events-none"></div>
            <div className="relative z-10">
              <LoadingSpinner />
              <p className="mt-6 text-base sm:text-lg text-gray-900 dark:text-gray-100 font-medium mb-2">
                {message}
              </p>
              {percentage > 0 && (
                <div className="mt-4 mb-2">
                  <div className="w-full bg-gray-200/50 dark:bg-gray-700/50 backdrop-blur-sm rounded-full h-2.5 overflow-hidden">
                    <div 
                      className="bg-gradient-to-r from-blue-500 to-purple-600 dark:from-blue-400 dark:to-purple-500 h-2.5 rounded-full transition-all duration-300 shadow-md relative overflow-hidden"
                      style={{ width: `${percentage}%` }}
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-white/30 to-transparent"></div>
                    </div>
                  </div>
                  <p className="mt-2 text-xs text-gray-600 dark:text-gray-400 font-medium">{percentage}%</p>
                </div>
              )}
              <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
                잠시만 기다려주세요
              </p>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error || (result && result.status === 'failed')) {
    return (
      <div className="min-h-screen flex items-center justify-center glass-bg dark:glass-bg-dark px-4 transition-colors relative overflow-hidden">
        {/* 배경 장식 요소 */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-red-400/10 dark:bg-red-500/10 rounded-full blur-3xl"></div>
        </div>
        
        <div className="text-center max-w-md w-full relative z-10">
          <div className="glass-elevated dark:glass-elevated-dark rounded-2xl p-6 sm:p-8 glass-transition relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-red-500/5 to-transparent pointer-events-none"></div>
            <div className="relative z-10">
              <div className="mb-4">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-red-50/80 dark:bg-red-900/30 backdrop-blur-xl rounded-full border border-red-200/50 dark:border-red-800/50 shadow-md">
                  <span className="text-3xl">⚠️</span>
                </div>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">
                분석 실패
              </h2>
              <p className="text-sm sm:text-base text-red-600 dark:text-red-400 mb-6">
                {error || result?.error || '분석에 실패했습니다.'}
              </p>
              <button
                onClick={() => navigate('/')}
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-500 dark:to-purple-500 text-white rounded-xl font-medium hover:from-blue-700 hover:to-purple-700 dark:hover:from-blue-600 dark:hover:to-purple-600 transition-all duration-200 shadow-lg backdrop-blur-sm relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent"></div>
                <span className="relative z-10">다시 시도</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (result && result.status === 'completed' && result.result) {
    return (
      <div>
        <div className="glass-elevated dark:glass-elevated-dark border-b border-gray-200/50 dark:border-gray-800/50 px-4 sm:px-6 py-3 sm:py-4 relative z-20">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="text-sm sm:text-base text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors backdrop-blur-sm px-3 py-1.5 rounded-lg hover:bg-white/20 dark:hover:bg-gray-800/20"
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

import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { analyzeService } from '../services/api'
import { AnalysisResult } from '../types'
import AnalysisReport from '../components/AnalysisReport'
import LoadingSpinner from '../components/LoadingSpinner'

function AnalysisPage() {
  const { analysisId } = useParams<{ analysisId: string }>()
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
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F5F5F5] px-4">
        <div className="text-center max-w-md w-full">
          <LoadingSpinner />
          <p className="mt-6 text-base sm:text-lg text-[#1A1A1A] font-medium mb-2">
            분석 중입니다...
          </p>
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
    return <AnalysisReport result={result.result} />
  }

  return null
}

export default AnalysisPage

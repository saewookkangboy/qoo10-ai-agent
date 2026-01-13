import { useEffect, useState } from 'react'
import { adminService } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import StatCard from '../components/admin/StatCard'
import LogViewer from '../components/admin/LogViewer'
import ScoreChart from '../components/admin/ScoreChart'
import AnalysisResultsList from '../components/admin/AnalysisResultsList'
import AIInsightReport from '../components/admin/AIInsightReport'

function AdminPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [scoreStats, setScoreStats] = useState<any>(null)
  const [analysisStats, setAnalysisStats] = useState<any>(null)
  const [analysisLogs, setAnalysisLogs] = useState<any>(null)
  const [errorLogs, setErrorLogs] = useState<any>(null)
  const [userLogs, setUserLogs] = useState<any>(null)
  const [analysisResults, setAnalysisResults] = useState<any>(null)
  const [aiReport, setAiReport] = useState<any>(null)

  useEffect(() => {
    loadAllData()
  }, [])

  const loadAllData = async () => {
    try {
      setLoading(true)
      
      const [scoreData, analysisData, logsData, errorsData, usersData, resultsData, reportData] = await Promise.all([
        adminService.getScoreStatistics(),
        adminService.getAnalysisStatistics(),
        adminService.getAnalysisLogs({ limit: 20 }),
        adminService.getErrorLogs({ limit: 20 }),
        adminService.getUserAnalysisLogs({ limit: 20 }),
        adminService.getAnalysisResultsList({ limit: 20 }),
        adminService.getAIInsightReport()
      ])
      
      setScoreStats(scoreData)
      setAnalysisStats(analysisData)
      setAnalysisLogs(logsData)
      setErrorLogs(errorsData)
      setUserLogs(usersData)
      setAnalysisResults(resultsData)
      setAiReport(reportData)
    } catch (error) {
      console.error('Failed to load admin data:', error)
      setError(error instanceof Error ? error.message : 'Failed to load admin data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F5F5F5]">
        <LoadingSpinner />
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F5F5F5]">
        <div className="text-center">
          <p className="text-red-500 text-lg font-medium">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#F5F5F5] py-4 sm:py-6 lg:py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 헤더 */}
        <div className="mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-[#1A1A1A] mb-2">
            관리자 대시보드
          </h1>
          <p className="text-sm sm:text-base text-[#4D4D4D]">
            시스템 통계, 로그, 분석 결과를 확인할 수 있습니다.
          </p>
        </div>

        {/* 통계 카드 그리드 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-6 sm:mb-8">
          <StatCard
            title="총 분석 수"
            value={analysisStats?.total_analyses || 0}
            subtitle="전체 분석 건수"
            icon="📊"
            color="blue"
          />
          <StatCard
            title="평균 점수"
            value={scoreStats?.overall?.avg_score ? Math.round(scoreStats.overall.avg_score) : 0}
            subtitle={`최대: ${scoreStats?.overall?.max_score || 0}점`}
            icon="⭐"
            color="green"
          />
          <StatCard
            title="고유 URL"
            value={analysisStats?.unique_urls || 0}
            subtitle="분석된 고유 URL 수"
            icon="🔗"
            color="purple"
          />
          <StatCard
            title="에러 발생"
            value={errorLogs?.total || 0}
            subtitle="최근 에러 로그"
            icon="⚠️"
            color="red"
          />
        </div>

        {/* AI 인사이트 리포트 */}
        {aiReport && (
          <div className="mb-6 sm:mb-8">
            <AIInsightReport report={aiReport} />
          </div>
        )}

        {/* 점수 통계 그래프 */}
        {scoreStats && (
          <div className="mb-6 sm:mb-8">
            <ScoreChart data={scoreStats} />
          </div>
        )}

        {/* 분석 결과 리스트 */}
        {analysisResults && (
          <div className="mb-6 sm:mb-8">
            <AnalysisResultsList results={analysisResults} />
          </div>
        )}

        {/* 로그 섹션 - 2열 그리드 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 sm:gap-8 mb-6 sm:mb-8">
          {/* 분석 로그 */}
          {analysisLogs && (
            <LogViewer
              title="분석 로그"
              logs={analysisLogs.logs}
              total={analysisLogs.total}
              type="analysis"
            />
          )}

          {/* 에러 로그 */}
          {errorLogs && (
            <LogViewer
              title="에러 로그"
              logs={errorLogs.logs}
              total={errorLogs.total}
              type="error"
            />
          )}
        </div>

        {/* 사용자 분석 로그 */}
        {userLogs && (
          <div className="mb-6 sm:mb-8">
            <LogViewer
              title="사용자 분석 로그"
              logs={userLogs.logs}
              total={userLogs.total}
              type="user"
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default AdminPage

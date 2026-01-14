import { useState } from 'react'
import { ProductAnalysis, Recommendation, ChecklistResult, CompetitorAnalysis } from '../types'
import ScoreCard from './ScoreCard'
import RecommendationCard from './RecommendationCard'
import ChecklistCard from './ChecklistCard'
import CompetitorComparisonCard from './CompetitorComparisonCard'
import DownloadButton from './DownloadButton'
import HelpTooltip from './HelpTooltip'
import ThemeToggle from './ThemeToggle'
import ScoreBarChart from './charts/ScoreBarChart'

interface AnalysisReportProps {
  result: {
    product_analysis?: ProductAnalysis
    shop_analysis?: any
    recommendations: Recommendation[]
    checklist?: ChecklistResult
    competitor_analysis?: CompetitorAnalysis
    product_data?: any
    shop_data?: any
  }
  analysisId?: string
}

function AnalysisReport({ result, analysisId }: AnalysisReportProps) {
  const { product_analysis, shop_analysis, recommendations, checklist, competitor_analysis } = result
  const overallScore = product_analysis?.overall_score || shop_analysis?.overall_score || 0
  const [activeTab, setActiveTab] = useState<'recommendations' | 'checklist'>('recommendations')

  const getScoreColor = (score: number) => {
    if (score >= 80) return {
      text: 'text-green-600 dark:text-green-400',
      bg: 'bg-green-50 dark:bg-green-900/20',
      border: 'border-green-500 dark:border-green-400',
      chartColor: '#00AA44'
    }
    if (score >= 60) return {
      text: 'text-yellow-600 dark:text-yellow-400',
      bg: 'bg-yellow-50 dark:bg-yellow-900/20',
      border: 'border-yellow-500 dark:border-yellow-400',
      chartColor: '#FF9900'
    }
    return {
      text: 'text-red-600 dark:text-red-400',
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-500 dark:border-red-400',
      chartColor: '#CC0000'
    }
  }

  const getScoreLabel = (score: number) => {
    if (score >= 80) return '양호'
    if (score >= 60) return '개선 필요'
    return '긴급 개선'
  }

  const colors = getScoreColor(overallScore)
  const highPriorityRecs = recommendations.filter(r => r.priority === 'high')
  const mediumPriorityRecs = recommendations.filter(r => r.priority === 'medium')
  const lowPriorityRecs = recommendations.filter(r => r.priority === 'low')

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 py-4 sm:py-6 lg:py-8 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 헤더 - 종합 점수 및 우선순위 */}
        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-4 sm:p-6 mb-4 sm:mb-6 transition-colors">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2 sm:mb-3">
                분석 리포트
              </h1>
              <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400">
                상품 분석 결과 및 개선 제안
              </p>
            </div>
            <ThemeToggle />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
            {/* 점수 카드 */}
            <div className={`px-4 sm:px-6 py-4 sm:py-6 rounded-xl ${colors.bg} border ${colors.border} flex flex-col justify-center hover:shadow-md transition-all duration-200`}>
              <div className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">종합 점수</div>
              <div className="flex items-baseline gap-1 mb-2">
                <span className={`text-3xl sm:text-4xl font-bold ${colors.text}`}>{overallScore}</span>
                <span className="text-base sm:text-lg text-gray-600 dark:text-gray-400">/ 100</span>
              </div>
              <div className={`text-xs sm:text-sm font-semibold ${colors.text} mt-1`}>
                {getScoreLabel(overallScore)}
              </div>
            </div>
            
            {/* 긴급 개선 항목 */}
            {highPriorityRecs.length > 0 && (
              <div className="px-4 sm:px-6 py-4 sm:py-6 bg-red-50 dark:bg-red-900/20 border border-red-500 dark:border-red-400 rounded-xl flex flex-col justify-center hover:shadow-md transition-all duration-200">
                <div className="text-xs sm:text-sm font-medium text-red-600 dark:text-red-400 mb-2">긴급 개선</div>
                <div className="text-2xl sm:text-3xl font-bold text-red-600 dark:text-red-400 mb-1">{highPriorityRecs.length}</div>
                <div className="text-xs text-gray-600 dark:text-gray-400">개 항목</div>
              </div>
            )}
          </div>
        </div>

        {/* 핵심 지표 카드 그리드 - 반응형 */}
        {product_analysis && (
          <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-4 sm:mb-6">
            <ScoreCard
              title="이미지"
              score={product_analysis.image_analysis.score}
              analysis={product_analysis.image_analysis}
            />
            <ScoreCard
              title="설명"
              score={product_analysis.description_analysis.score}
              analysis={product_analysis.description_analysis}
            />
            <ScoreCard
              title="가격"
              score={product_analysis.price_analysis.score}
              analysis={product_analysis.price_analysis}
            />
            <ScoreCard
              title="리뷰"
              score={product_analysis.review_analysis.score}
              analysis={product_analysis.review_analysis}
            />
          </div>
            
            {/* 점수 비교 바 차트 */}
            <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-4 sm:p-6 mb-4 sm:mb-6 transition-colors">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
                📊 점수 비교
              </h2>
              <ScoreBarChart
                data={[
                  { category: '이미지', score: product_analysis.image_analysis.score, color: '#0066CC' },
                  { category: '설명', score: product_analysis.description_analysis.score, color: '#00AA44' },
                  { category: '가격', score: product_analysis.price_analysis.score, color: '#FF9900' },
                  { category: '리뷰', score: product_analysis.review_analysis.score, color: '#CC0000' },
                ]}
                height={250}
              />
            </div>
          </>
        )}

        {/* 탭 기반 결과 섹션 */}
        <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-4 sm:p-6 transition-colors">
          {/* 탭 헤더 */}
          <div className="flex items-center gap-2 mb-4 sm:mb-6">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
              분석 결과
            </h2>
          </div>

          {/* 탭 네비게이션 */}
          <div className="flex border-b border-gray-200 dark:border-gray-700 mb-4 sm:mb-6">
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`px-4 sm:px-6 py-3 sm:py-4 text-sm sm:text-base font-semibold transition-colors ${
                activeTab === 'recommendations'
                  ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
              }`}
            >
              💡 매출 강화 아이디어
            </button>
            {checklist && (
              <button
                onClick={() => setActiveTab('checklist')}
                className={`px-4 sm:px-6 py-3 sm:py-4 text-sm sm:text-base font-semibold transition-colors ${
                  activeTab === 'checklist'
                    ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
                }`}
              >
                📋 메뉴얼 기반 체크리스트
              </button>
            )}
          </div>

          {/* 탭 컨텐츠 */}
          <div>
            {/* 매출 강화 아이디어 탭 */}
            {activeTab === 'recommendations' && (
              <div>
                <div className="flex items-center gap-2 mb-4 sm:mb-6">
                  <HelpTooltip 
                    content="Qoo10 큐텐 대학의 판매 노하우를 기반으로 한 개선 제안입니다.\n\n• High Priority: 즉시 개선이 필요한 항목\n• Medium Priority: 단기적으로 개선하면 효과를 볼 수 있는 항목\n• Low Priority: 장기적으로 고려하면 좋은 개선 사항\n\n각 제안을 단계적으로 실행하시면 매출 증대에 도움이 됩니다." 
                  />
                </div>
                
                {/* High Priority */}
                {highPriorityRecs.length > 0 && (
                  <div className="mb-6 sm:mb-8">
                    <div className="flex items-center gap-3 mb-4 sm:mb-5">
                      <div className="w-2 h-2 rounded-full bg-red-500"></div>
                      <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">High Priority</h3>
                      <span className="px-2.5 py-1 text-xs font-semibold bg-red-600 dark:bg-red-500 text-white rounded-lg">
                        {highPriorityRecs.length}
                      </span>
                    </div>
                    <div className="space-y-4 sm:space-y-5">
                      {highPriorityRecs.map((rec) => (
                        <RecommendationCard key={rec.id} recommendation={rec} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Medium Priority */}
                {mediumPriorityRecs.length > 0 && (
                  <div className="mb-6 sm:mb-8">
                    <div className="flex items-center gap-3 mb-4 sm:mb-5">
                      <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                      <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">Medium Priority</h3>
                      <span className="px-2.5 py-1 text-xs font-semibold bg-yellow-600 dark:bg-yellow-500 text-white rounded-lg">
                        {mediumPriorityRecs.length}
                      </span>
                    </div>
                    <div className="space-y-4 sm:space-y-5">
                      {mediumPriorityRecs.map((rec) => (
                        <RecommendationCard key={rec.id} recommendation={rec} />
                      ))}
                    </div>
                  </div>
                )}

                {/* Low Priority */}
                {lowPriorityRecs.length > 0 && (
                  <div>
                    <div className="flex items-center gap-3 mb-4 sm:mb-5">
                      <div className="w-2 h-2 rounded-full bg-gray-500"></div>
                      <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">Low Priority</h3>
                      <span className="px-2.5 py-1 text-xs font-semibold bg-gray-600 dark:bg-gray-500 text-white rounded-lg">
                        {lowPriorityRecs.length}
                      </span>
                    </div>
                    <div className="space-y-4 sm:space-y-5">
                      {lowPriorityRecs.map((rec) => (
                        <RecommendationCard key={rec.id} recommendation={rec} />
                      ))}
                    </div>
                  </div>
                )}

                {recommendations.length === 0 && (
                  <div className="text-center py-8 sm:py-12">
                    <p className="text-gray-600 dark:text-gray-400 text-sm sm:text-base">개선 제안이 없습니다.</p>
                  </div>
                )}
              </div>
            )}

            {/* 메뉴얼 기반 체크리스트 탭 */}
            {activeTab === 'checklist' && checklist && (
              <div className="mt-4">
                <ChecklistCard checklist={checklist} />
              </div>
            )}
          </div>
        </div>

        {/* 경쟁사 비교 카드 (Phase 2) */}
        {competitor_analysis && (
          <div className="mt-4 sm:mt-6">
            <CompetitorComparisonCard competitorAnalysis={competitor_analysis} />
          </div>
        )}

        {/* 리포트 다운로드 버튼 (Phase 2) - 숨김 처리 */}
        {false && analysisId && (
        <div className="mt-4 sm:mt-6 bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-4 sm:p-6 transition-colors">
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            📥 리포트 다운로드
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            분석 결과를 PDF, Excel, 또는 Markdown 형식으로 다운로드할 수 있습니다.
          </p>
          <div className="flex flex-wrap gap-3">
            <DownloadButton format="pdf" label="PDF 다운로드" color="bg-red-600 hover:bg-red-700" analysisId={analysisId!} />
            <DownloadButton format="excel" label="Excel 다운로드" color="bg-green-600 hover:bg-green-700" analysisId={analysisId!} />
            <DownloadButton format="markdown" label="Markdown 다운로드" color="bg-blue-600 hover:bg-blue-700" analysisId={analysisId!} />
          </div>
        </div>
        )}
      </div>
    </div>
  )
}

export default AnalysisReport

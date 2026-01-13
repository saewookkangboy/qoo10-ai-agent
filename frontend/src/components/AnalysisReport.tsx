import { ProductAnalysis, Recommendation, ChecklistResult, CompetitorAnalysis } from '../types'
import ScoreCard from './ScoreCard'
import RecommendationCard from './RecommendationCard'
import ChecklistCard from './ChecklistCard'
import CompetitorComparisonCard from './CompetitorComparisonCard'
import DownloadButton from './DownloadButton'

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

  const getScoreColor = (score: number) => {
    if (score >= 80) return {
      text: 'text-[#00AA44]',
      bg: 'bg-green-50',
      border: 'border-[#00AA44]'
    }
    if (score >= 60) return {
      text: 'text-[#FF9900]',
      bg: 'bg-yellow-50',
      border: 'border-[#FF9900]'
    }
    return {
      text: 'text-[#CC0000]',
      bg: 'bg-red-50',
      border: 'border-[#CC0000]'
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
    <div className="min-h-screen bg-[#F5F5F5] py-4 sm:py-6 lg:py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* 헤더 - 종합 점수 및 우선순위 */}
        <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6 mb-4 sm:mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-[#1A1A1A] mb-2 sm:mb-3">
                분석 리포트
              </h1>
              <p className="text-sm sm:text-base text-[#4D4D4D]">
                상품 분석 결과 및 개선 제안
              </p>
            </div>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 sm:gap-4">
              <div className={`px-4 sm:px-6 py-3 sm:py-4 rounded-lg ${colors.bg} border-2 ${colors.border}`}>
                <div className="text-xs sm:text-sm text-[#4D4D4D] mb-1">종합 점수</div>
                <div className="flex items-baseline gap-1">
                  <span className={`text-3xl sm:text-4xl font-bold ${colors.text}`}>{overallScore}</span>
                  <span className="text-base sm:text-lg text-[#4D4D4D]">/ 100</span>
                </div>
                <div className={`text-xs sm:text-sm font-medium ${colors.text} mt-1`}>
                  {getScoreLabel(overallScore)}
                </div>
              </div>
              {highPriorityRecs.length > 0 && (
                <div className="px-3 sm:px-4 py-2 sm:py-3 bg-red-50 border-2 border-[#CC0000] rounded-lg">
                  <div className="text-xs sm:text-sm text-[#CC0000] font-medium mb-1">긴급 개선</div>
                  <div className="text-xl sm:text-2xl font-bold text-[#CC0000]">{highPriorityRecs.length}</div>
                  <div className="text-xs text-[#4D4D4D]">개 항목</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* 핵심 지표 카드 그리드 - 반응형 */}
        {product_analysis && (
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
        )}

        {/* 개선 제안 - 우선순위별 그룹핑 */}
        <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6">
          <h2 className="text-xl sm:text-2xl font-bold text-[#1A1A1A] mb-4 sm:mb-6">
            💡 매출 강화 아이디어
          </h2>
          
          {/* High Priority */}
          {highPriorityRecs.length > 0 && (
            <div className="mb-6 sm:mb-8">
              <div className="flex items-center gap-2 mb-3 sm:mb-4">
                <span className="text-lg sm:text-xl">🔴</span>
                <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A]">High Priority</h3>
                <span className="px-2 py-0.5 text-xs font-medium bg-[#CC0000] text-white rounded">
                  {highPriorityRecs.length}
                </span>
              </div>
              <div className="space-y-3 sm:space-y-4">
                {highPriorityRecs.map((rec) => (
                  <RecommendationCard key={rec.id} recommendation={rec} />
                ))}
              </div>
            </div>
          )}

          {/* Medium Priority */}
          {mediumPriorityRecs.length > 0 && (
            <div className="mb-6 sm:mb-8">
              <div className="flex items-center gap-2 mb-3 sm:mb-4">
                <span className="text-lg sm:text-xl">🟡</span>
                <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A]">Medium Priority</h3>
                <span className="px-2 py-0.5 text-xs font-medium bg-[#FF9900] text-white rounded">
                  {mediumPriorityRecs.length}
                </span>
              </div>
              <div className="space-y-3 sm:space-y-4">
                {mediumPriorityRecs.map((rec) => (
                  <RecommendationCard key={rec.id} recommendation={rec} />
                ))}
              </div>
            </div>
          )}

          {/* Low Priority */}
          {lowPriorityRecs.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3 sm:mb-4">
                <span className="text-lg sm:text-xl">🟢</span>
                <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A]">Low Priority</h3>
                <span className="px-2 py-0.5 text-xs font-medium bg-[#808080] text-white rounded">
                  {lowPriorityRecs.length}
                </span>
              </div>
              <div className="space-y-3 sm:space-y-4">
                {lowPriorityRecs.map((rec) => (
                  <RecommendationCard key={rec.id} recommendation={rec} />
                ))}
              </div>
            </div>
          )}

          {recommendations.length === 0 && (
            <div className="text-center py-8 sm:py-12">
              <p className="text-[#4D4D4D] text-sm sm:text-base">개선 제안이 없습니다.</p>
            </div>
          )}
        </div>

        {/* 체크리스트 카드 (Phase 2) */}
        {checklist && (
          <div className="mt-4 sm:mt-6">
            <ChecklistCard checklist={checklist} />
          </div>
        )}

        {/* 경쟁사 비교 카드 (Phase 2) */}
        {competitor_analysis && (
          <div className="mt-4 sm:mt-6">
            <CompetitorComparisonCard competitorAnalysis={competitor_analysis} />
          </div>
        )}

        {/* 리포트 다운로드 버튼 (Phase 2) */}
        <div className="mt-4 sm:mt-6 bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6">
          <h2 className="text-xl sm:text-2xl font-bold text-[#1A1A1A] mb-4">
            📥 리포트 다운로드
          </h2>
          <p className="text-sm text-[#4D4D4D] mb-4">
            분석 결과를 PDF, Excel, 또는 Markdown 형식으로 다운로드할 수 있습니다.
          </p>
          <div className="flex flex-wrap gap-3">
            {analysisId && (
              <>
                <DownloadButton format="pdf" label="PDF 다운로드" color="bg-red-600 hover:bg-red-700" analysisId={analysisId} />
                <DownloadButton format="excel" label="Excel 다운로드" color="bg-green-600 hover:bg-green-700" analysisId={analysisId} />
                <DownloadButton format="markdown" label="Markdown 다운로드" color="bg-blue-600 hover:bg-blue-700" analysisId={analysisId} />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AnalysisReport

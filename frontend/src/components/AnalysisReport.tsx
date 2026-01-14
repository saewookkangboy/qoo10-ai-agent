import { useState } from 'react'
import { ProductAnalysis, Recommendation, ChecklistResult, CompetitorAnalysis } from '../types'
import ScoreCard from './ScoreCard'
import RecommendationCard from './RecommendationCard'
import ChecklistCard from './ChecklistCard'
import CompetitorComparisonCard from './CompetitorComparisonCard'
import DownloadButton from './DownloadButton'
import HelpTooltip from './HelpTooltip'
import ThemeToggle from './ThemeToggle'
import ScoreGaugeChart from './charts/ScoreGaugeChart'
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
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* 종합 점수 게이지 차트 */}
            <div className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
              <div className="text-center mb-2">
                <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-2">종합 점수</p>
                <ScoreGaugeChart 
                  score={overallScore} 
                  title={getScoreLabel(overallScore)}
                  color={colors.chartColor}
                  size={180}
                />
              </div>
            </div>
            
            {/* 점수 카드 */}
            <div className={`px-4 sm:px-6 py-3 sm:py-4 rounded-lg ${colors.bg} border-2 ${colors.border} flex flex-col justify-center`}>
              <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 mb-1">종합 점수</div>
                <div className="flex items-baseline gap-1">
                  <span className={`text-3xl sm:text-4xl font-bold ${colors.text}`}>{overallScore}</span>
                <span className="text-base sm:text-lg text-gray-600 dark:text-gray-400">/ 100</span>
                </div>
                <div className={`text-xs sm:text-sm font-medium ${colors.text} mt-1`}>
                  {getScoreLabel(overallScore)}
                </div>
              </div>
            
            {/* 긴급 개선 항목 */}
              {highPriorityRecs.length > 0 && (
              <div className="px-3 sm:px-4 py-2 sm:py-3 bg-red-50 dark:bg-red-900/20 border-2 border-red-500 dark:border-red-400 rounded-lg flex flex-col justify-center">
                <div className="text-xs sm:text-sm text-red-600 dark:text-red-400 font-medium mb-1">긴급 개선</div>
                <div className="text-xl sm:text-2xl font-bold text-red-600 dark:text-red-400">{highPriorityRecs.length}</div>
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

        {/* 페이지 구조 분석 카드 */}
        {product_analysis?.page_structure_analysis && (
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-4 sm:p-6 mb-4 sm:mb-6 transition-colors">
            <div className="flex items-center gap-2 mb-4">
              <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                📐 페이지 구조 분석
              </h2>
              <HelpTooltip 
                content="페이지의 모든 div class를 분석하여 구조적 완성도를 평가합니다.\n\n• 총 클래스 수: 페이지의 구조 복잡도\n• 주요 요소 존재 여부: 필수 정보 요소 확인\n• 구조 완성도: 각 정보 요소의 완성도 평가" 
              />
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">총 클래스 수</div>
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {product_analysis.page_structure_analysis.total_classes}
                </div>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">구조 점수</div>
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {product_analysis.page_structure_analysis.score}
                  <span className="text-base text-gray-600 dark:text-gray-400">/ 100</span>
                </div>
              </div>
              
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">완성된 요소</div>
                <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {Object.values(product_analysis.page_structure_analysis.structure_completeness).filter(v => v).length}
                  <span className="text-base text-gray-600 dark:text-gray-400">/ {Object.keys(product_analysis.page_structure_analysis.structure_completeness).length}</span>
                </div>
              </div>
            </div>

            {/* 주요 요소 존재 여부 */}
            <div className="mb-4">
              <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-2">주요 요소 확인</h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
                {Object.entries(product_analysis.page_structure_analysis.key_elements_present).map(([key, present]) => (
                  <div key={key} className="flex items-center gap-2">
                    <span className={present ? "text-green-500 dark:text-green-400" : "text-red-500 dark:text-red-400"}>
                      {present ? "✓" : "✗"}
                    </span>
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* 상위 클래스 목록 */}
            {product_analysis.page_structure_analysis.top_classes && 
             product_analysis.page_structure_analysis.top_classes.length > 0 && (
              <div className="mb-4">
                <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-2">주요 사용 클래스 (상위 10개)</h3>
                <div className="flex flex-wrap gap-2">
                  {product_analysis.page_structure_analysis.top_classes.map((item, idx) => (
                    <div 
                      key={idx}
                      className="px-3 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-full text-sm border border-blue-200 dark:border-blue-800"
                      title={`사용 횟수: ${item.frequency}`}
                    >
                      {item.class} ({item.frequency})
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 추천 사항 */}
            {product_analysis.page_structure_analysis.recommendations.length > 0 && (
              <div>
                <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 mb-2">구조 개선 제안</h3>
                <ul className="list-disc list-inside space-y-1">
                  {product_analysis.page_structure_analysis.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-sm text-gray-600 dark:text-gray-400">{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
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
                    <div className="flex items-center gap-2 mb-3 sm:mb-4">
                      <span className="text-lg sm:text-xl">🔴</span>
                      <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">High Priority</h3>
                      <span className="px-2 py-0.5 text-xs font-medium bg-red-600 dark:bg-red-500 text-white rounded">
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
                      <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">Medium Priority</h3>
                      <span className="px-2 py-0.5 text-xs font-medium bg-yellow-600 dark:bg-yellow-500 text-white rounded">
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
                      <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">Low Priority</h3>
                      <span className="px-2 py-0.5 text-xs font-medium bg-gray-600 dark:bg-gray-500 text-white rounded">
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

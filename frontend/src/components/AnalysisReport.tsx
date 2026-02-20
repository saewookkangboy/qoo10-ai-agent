import { useState } from 'react'
import { ProductAnalysis, Recommendation, ChecklistResult, CompetitorAnalysis, ValidationResult, ProductData, ShopAnalysis, ShopData } from '../types'
import ScoreCard from './ScoreCard'
import RecommendationCard from './RecommendationCard'
import ChecklistCard from './ChecklistCard'
import CompetitorComparisonCard from './CompetitorComparisonCard'
import DownloadButton from './DownloadButton'
import HelpTooltip from './HelpTooltip'
import ThemeToggle from './ThemeToggle'
import ValidationModal from './ValidationModal'
import ChatBot from './ChatBot'

interface AnalysisReportProps {
  result: {
    product_analysis?: ProductAnalysis
    shop_analysis?: ShopAnalysis
    recommendations: Recommendation[]
    checklist?: ChecklistResult
    competitor_analysis?: CompetitorAnalysis
    product_data?: ProductData
    shop_data?: ShopData
    validation?: ValidationResult
  }
  analysisId?: string
}

// Safe score access for partial API responses (e.g. HTTP fallback)
const safeScore = (obj: { score?: number } | null | undefined): number =>
  (obj != null && typeof obj === 'object' && typeof (obj as any).score === 'number')
    ? (obj as any).score
    : 0

function AnalysisReport({ result, analysisId }: AnalysisReportProps) {
  const { product_analysis, shop_analysis, recommendations, checklist, competitor_analysis, validation } = result
  const overallScore = product_analysis?.overall_score ?? shop_analysis?.overall_score ?? 0
  const [activeTab, setActiveTab] = useState<'recommendations' | 'checklist'>('recommendations')
  const [isValidationModalOpen, setIsValidationModalOpen] = useState(false)

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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900/50 py-6 lg:py-8 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800/80 p-4 sm:p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
                분석 리포트
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                {product_analysis ? '상품 분석 결과 및 개선 제안' : shop_analysis ? '샵 분석 결과 및 개선 제안' : '분석 결과 및 개선 제안'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {validation && (
                <button
                  onClick={() => setIsValidationModalOpen(true)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border ${
                    validation.is_valid
                      ? 'border-green-200 dark:border-green-800 text-green-700 dark:text-green-300 bg-green-50 dark:bg-green-900/20'
                      : 'border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/20'
                  }`}
                >
                  {validation.is_valid ? '검증 통과' : `검증 ${(validation.validation_score ?? 0).toFixed(0)}%`}
                </button>
              )}
              <ThemeToggle />
            </div>
          </div>
          
          {validation && (
            <button
              onClick={() => setIsValidationModalOpen(true)}
              className="w-full flex items-center justify-between py-3 px-4 rounded-lg border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50 text-left hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors mb-6"
            >
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">데이터 검증</span>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {(validation.validation_score ?? 0).toFixed(1)}%
                {validation.mismatches?.length ? ` · 불일치 ${validation.mismatches.length}건` : ''}
                {validation.missing_items?.length ? ` · 누락 ${validation.missing_items.length}건` : ''}
              </span>
              <span className="text-gray-400 dark:text-gray-500">→</span>
            </button>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={`rounded-xl border px-5 py-4 ${colors.border} ${colors.bg}`}>
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">종합 점수</div>
              <div className="flex items-baseline gap-1.5 mt-1">
                <span className={`text-3xl font-bold ${colors.text}`}>{overallScore}</span>
                <span className="text-gray-500 dark:text-gray-400">/ 100</span>
              </div>
              <div className={`text-sm font-medium mt-1 ${colors.text}`}>{getScoreLabel(overallScore)}</div>
            </div>
            {highPriorityRecs.length > 0 ? (
              <div className="rounded-xl border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-5 py-4">
                <div className="text-xs font-medium text-red-600 dark:text-red-400 uppercase tracking-wide">긴급 개선</div>
                <div className="text-2xl font-bold text-red-600 dark:text-red-400 mt-1">{highPriorityRecs.length}</div>
                <div className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">개 항목</div>
              </div>
            ) : (
              <div className="rounded-xl border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50 px-5 py-4">
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">긴급 개선</div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">없음</div>
              </div>
            )}
          </div>
        </div>

        {/* 핵심 지표 카드 */}
        {product_analysis && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {product_analysis.image_analysis != null && (
              <ScoreCard
                title="이미지"
                score={safeScore(product_analysis.image_analysis)}
                analysis={product_analysis.image_analysis}
              />
            )}
            {product_analysis.description_analysis != null && (
              <ScoreCard
                title="설명"
                score={safeScore(product_analysis.description_analysis)}
                analysis={product_analysis.description_analysis}
              />
            )}
            {product_analysis.price_analysis != null && (
              <ScoreCard
                title="가격"
                score={safeScore(product_analysis.price_analysis)}
                analysis={product_analysis.price_analysis}
              />
            )}
            {product_analysis.review_analysis != null && (
              <ScoreCard
                title="리뷰"
                score={safeScore(product_analysis.review_analysis)}
                analysis={product_analysis.review_analysis}
              />
            )}
          </div>
        )}

        {shop_analysis && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {shop_analysis.shop_info != null && (
              <ScoreCard
                title="샵 정보"
                score={safeScore(shop_analysis.shop_info)}
                analysis={shop_analysis.shop_info}
              />
            )}
            {shop_analysis.product_analysis != null && (
              <ScoreCard
                title="상품 분석"
                score={safeScore(shop_analysis.product_analysis)}
                analysis={shop_analysis.product_analysis}
              />
            )}
            {shop_analysis.category_analysis != null && (
              <ScoreCard
                title="카테고리"
                score={safeScore(shop_analysis.category_analysis)}
                analysis={shop_analysis.category_analysis}
              />
            )}
            {shop_analysis.level_analysis != null && (
              <ScoreCard
                title="레벨 분석"
                score={safeScore(shop_analysis.level_analysis)}
                analysis={shop_analysis.level_analysis}
              />
            )}
          </div>
        )}

        {/* 분석 결과 탭 */}
        <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800/80 p-4 sm:p-6">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">분석 결과</h2>
          <div className="flex gap-1 border-b border-gray-200 dark:border-gray-600 mb-6">
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`px-4 py-3 text-sm font-medium rounded-t-lg transition-colors ${
                activeTab === 'recommendations'
                  ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-b-2 border-blue-500 -mb-px'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              매출 강화 아이디어
            </button>
            {checklist && (
              <button
                onClick={() => setActiveTab('checklist')}
                className={`px-4 py-3 text-sm font-medium rounded-t-lg transition-colors ${
                  activeTab === 'checklist'
                    ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border-b-2 border-blue-500 -mb-px'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                }`}
              >
                메뉴얼 체크리스트
              </button>
            )}
          </div>

          <div>
            {activeTab === 'recommendations' && (
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <HelpTooltip content="Qoo10 큐텐 대학의 판매 노하우를 기반으로 한 개선 제안입니다. High: 즉시 개선, Medium: 단기 개선, Low: 장기 검토." />
                </div>
                {highPriorityRecs.length > 0 && (
                  <section className="mb-8">
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-3 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500" /> High · {highPriorityRecs.length}건
                    </h3>
                    <div className="space-y-4">
                      {highPriorityRecs.map((rec, i) => (
                        <RecommendationCard key={`high-${i}-${rec.id ?? ''}`} recommendation={rec} />
                      ))}
                    </div>
                  </section>
                )}
                {mediumPriorityRecs.length > 0 && (
                  <section className="mb-8">
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-3 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500" /> Medium · {mediumPriorityRecs.length}건
                    </h3>
                    <div className="space-y-4">
                      {mediumPriorityRecs.map((rec, i) => (
                        <RecommendationCard key={`medium-${i}-${rec.id ?? ''}`} recommendation={rec} />
                      ))}
                    </div>
                  </section>
                )}
                {lowPriorityRecs.length > 0 && (
                  <section>
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-3 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-gray-400" /> Low · {lowPriorityRecs.length}건
                    </h3>
                    <div className="space-y-4">
                      {lowPriorityRecs.map((rec, i) => (
                        <RecommendationCard key={`low-${i}-${rec.id ?? ''}`} recommendation={rec} />
                      ))}
                    </div>
                  </section>
                )}
                {recommendations.length === 0 && (
                  <p className="text-center py-10 text-gray-500 dark:text-gray-400 text-sm">개선 제안이 없습니다.</p>
                )}
              </div>
            )}

            {/* 메뉴얼 기반 체크리스트 탭 */}
            {activeTab === 'checklist' && checklist && (
              <div className="mt-4">
                <ChecklistCard 
                  checklist={checklist} 
                  analysisId={analysisId}
                  productData={result.product_data}
                  shopData={result.shop_data}
                />
              </div>
            )}
          </div>
        </div>

        {competitor_analysis && (
          <div className="mt-6">
            <CompetitorComparisonCard competitorAnalysis={competitor_analysis} />
          </div>
        )}

        {analysisId && (
          <div className="mt-6 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800/80 p-4 sm:p-6">
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">리포트 다운로드</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">PDF, Excel, Markdown 형식으로 저장할 수 있습니다.</p>
            <div className="flex flex-wrap gap-2">
              <DownloadButton format="pdf" label="PDF" color="bg-red-600 hover:bg-red-700" analysisId={analysisId} />
              <DownloadButton format="excel" label="Excel" color="bg-green-600 hover:bg-green-700" analysisId={analysisId} />
              <DownloadButton format="markdown" label="Markdown" color="bg-blue-600 hover:bg-blue-700" analysisId={analysisId} />
            </div>
          </div>
        )}
      </div>

      {/* Validation Modal */}
      {validation && (
        <ValidationModal
          validation={validation}
          analysisId={analysisId}
          isOpen={isValidationModalOpen}
          onClose={() => setIsValidationModalOpen(false)}
        />
      )}

      {/* AI 챗봇 */}
      <ChatBot
        analysisResult={result}
        analysisId={analysisId}
      />
    </div>
  )
}

export default AnalysisReport

import { CompetitorAnalysis } from '../types'
import HelpTooltip from './HelpTooltip'

interface CompetitorComparisonCardProps {
  competitorAnalysis: CompetitorAnalysis
}

const helpContent = '경쟁사 비교 분석은 히트 상품을 만드는 핵심 방법입니다.\n\n• 가격 포지셔닝: 경쟁사 대비 가격 경쟁력을 파악합니다\n• 평점 포지셔닝: 상품 품질과 고객 만족도를 비교합니다\n• 리뷰 포지셔닝: 고객 신뢰도와 인기도를 분석합니다\n\n차별화 포인트를 찾아 경쟁 우위를 확보하고, 경쟁사 분석 기반 제안을 통해 매출을 증대시킬 수 있습니다.'

function CompetitorComparisonCard({ competitorAnalysis }: CompetitorComparisonCardProps) {
  // 안전한 기본값 처리
  if (!competitorAnalysis) {
    return (
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-4 sm:p-6 transition-colors">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4 sm:mb-6">
          🔍 경쟁사 비교 분석
        </h2>
        <p className="text-gray-600 dark:text-gray-400">경쟁사 분석 데이터가 없습니다.</p>
      </div>
    )
  }

  const { 
    target_product, 
    competitors = [], 
    comparison, 
    differentiation_points = [], 
    recommendations = [] 
  } = competitorAnalysis

  // comparison이 없을 경우 기본값 설정
  const safeComparison = comparison || {
    price_position: 'average',
    price_stats: { target: 0, average: 0, min: 0, max: 0 },
    rating_position: 'average',
    rating_stats: { target: 0, average: 0 },
    review_position: 'average',
    review_stats: { target: 0, average: 0 }
  }

  const getPositionColor = (position: string) => {
    const colors: Record<string, string> = {
      excellent: 'text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20',
      above_average: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20',
      average: 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20',
      below_average: 'text-orange-600 dark:text-orange-400 bg-orange-50 dark:bg-orange-900/20',
      poor: 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20',
      lowest: 'text-purple-600 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20',
      highest: 'text-pink-600 dark:text-pink-400 bg-pink-50 dark:bg-pink-900/20'
    }
    return colors[position] || 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800'
  }

  const getPositionLabel = (position: string) => {
    const labels: Record<string, string> = {
      excellent: '우수',
      above_average: '평균 이상',
      average: '평균',
      below_average: '평균 이하',
      poor: '낮음',
      lowest: '최저가',
      highest: '최고가'
    }
    return labels[position] || position
  }

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-4 sm:p-6 transition-colors">
      <div className="flex items-center gap-2 mb-6">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-gray-100">
          🔍 경쟁사 비교 분석
        </h2>
        <HelpTooltip content={helpContent} />
      </div>

      {/* 비교 요약 */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 mb-6">
        <div className={`p-4 sm:p-5 rounded-xl border border-gray-200 dark:border-gray-700 ${getPositionColor(safeComparison.price_position)} hover:shadow-md transition-all duration-200`}>
          <div className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">가격 포지셔닝</div>
          <div className="text-lg sm:text-xl font-bold mb-1">{getPositionLabel(safeComparison.price_position)}</div>
          <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
            평균: {safeComparison.price_stats?.average != null ? safeComparison.price_stats.average.toLocaleString() : 'N/A'}엔
          </div>
        </div>

        <div className={`p-4 sm:p-5 rounded-xl border border-gray-200 dark:border-gray-700 ${getPositionColor(safeComparison.rating_position)} hover:shadow-md transition-all duration-200`}>
          <div className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">평점 포지셔닝</div>
          <div className="text-lg sm:text-xl font-bold mb-1">{getPositionLabel(safeComparison.rating_position)}</div>
          <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
            평균: {safeComparison.rating_stats?.average != null ? safeComparison.rating_stats.average.toFixed(1) : 'N/A'}점
          </div>
        </div>

        <div className={`p-4 sm:p-5 rounded-xl border border-gray-200 dark:border-gray-700 ${getPositionColor(safeComparison.review_position)} hover:shadow-md transition-all duration-200`}>
          <div className="text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">리뷰 포지셔닝</div>
          <div className="text-lg sm:text-xl font-bold mb-1">{getPositionLabel(safeComparison.review_position)}</div>
          <div className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
            평균: {safeComparison.review_stats?.average != null ? safeComparison.review_stats.average.toLocaleString() : 'N/A'}개
          </div>
        </div>
      </div>

      {/* 차별화 포인트 */}
      {differentiation_points.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
            차별화 포인트
          </h3>
          <div className="flex flex-wrap gap-2 sm:gap-3">
            {differentiation_points.map((point, idx) => (
              <span
                key={idx}
                className="px-3 py-1.5 text-xs sm:text-sm font-medium bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-lg border border-blue-200 dark:border-blue-800 hover:shadow-sm transition-all"
              >
                ✨ {point}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 경쟁사 상위 5개 비교 테이블 */}
      {competitors.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            경쟁사 Top 5 비교
          </h3>
          <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
                  <th className="text-left py-3 px-4 text-gray-600 dark:text-gray-400 font-semibold">순위</th>
                  <th className="text-left py-3 px-4 text-gray-600 dark:text-gray-400 font-semibold">상품명</th>
                  <th className="text-right py-3 px-4 text-gray-600 dark:text-gray-400 font-semibold">가격</th>
                  <th className="text-right py-3 px-4 text-gray-600 dark:text-gray-400 font-semibold">평점</th>
                  <th className="text-right py-3 px-4 text-gray-600 dark:text-gray-400 font-semibold">리뷰</th>
                </tr>
              </thead>
              <tbody>
                {/* 타겟 상품 (강조) */}
                {target_product && (
                  <tr className="bg-blue-50 dark:bg-blue-900/20 border-b border-gray-200 dark:border-gray-700">
                    <td className="py-3 px-4 font-semibold text-blue-600 dark:text-blue-400">내 상품</td>
                    <td className="py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                      {target_product.product_name || 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-gray-900 dark:text-gray-100">
                      {target_product.price != null ? target_product.price.toLocaleString() : 'N/A'}엔
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-gray-900 dark:text-gray-100">
                      {target_product.rating != null ? target_product.rating.toFixed(1) : 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-gray-900 dark:text-gray-100">
                      {target_product.review_count != null ? target_product.review_count.toLocaleString() : 'N/A'}
                    </td>
                  </tr>
                )}
                {/* 경쟁사 상위 5개 */}
                {competitors.slice(0, 5).map((competitor, idx) => (
                  <tr key={competitor?.rank || idx} className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                    <td className="py-3 px-4 text-gray-600 dark:text-gray-400">#{competitor?.rank || idx + 1}</td>
                    <td className="py-3 px-4 text-gray-900 dark:text-gray-100">{competitor?.product_name || 'N/A'}</td>
                    <td className="py-3 px-4 text-right text-gray-900 dark:text-gray-100">
                      {competitor?.price != null ? competitor.price.toLocaleString() : 'N/A'}엔
                    </td>
                    <td className="py-3 px-4 text-right text-gray-900 dark:text-gray-100">
                      {competitor?.rating != null ? competitor.rating.toFixed(1) : 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                      {competitor?.review_count != null ? competitor.review_count.toLocaleString() : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 경쟁사 분석 기반 추천 */}
      {recommendations.length > 0 && (
        <div>
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            경쟁사 분석 기반 제안
          </h3>
          <div className="space-y-4">
            {recommendations.map((rec, idx) => (
              <div key={idx} className="p-4 sm:p-5 bg-yellow-50 dark:bg-yellow-900/20 border-l-4 border-yellow-500 dark:border-yellow-400 rounded-xl border border-yellow-200 dark:border-yellow-800 hover:shadow-md transition-all duration-200">
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">{rec.title}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{rec.description}</p>
                {rec.action_items && (
                  <ul className="text-sm text-gray-900 dark:text-gray-100 space-y-2">
                    {rec.action_items.map((item, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-yellow-600 dark:text-yellow-400 mt-0.5">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default CompetitorComparisonCard

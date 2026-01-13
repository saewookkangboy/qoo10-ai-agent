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
      <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6">
        <h2 className="text-xl sm:text-2xl font-bold text-[#1A1A1A] mb-4 sm:mb-6">
          🔍 경쟁사 비교 분석
        </h2>
        <p className="text-[#4D4D4D]">경쟁사 분석 데이터가 없습니다.</p>
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
      excellent: 'text-green-600 bg-green-50',
      above_average: 'text-blue-600 bg-blue-50',
      average: 'text-yellow-600 bg-yellow-50',
      below_average: 'text-orange-600 bg-orange-50',
      poor: 'text-red-600 bg-red-50',
      lowest: 'text-purple-600 bg-purple-50',
      highest: 'text-pink-600 bg-pink-50'
    }
    return colors[position] || 'text-gray-600 bg-gray-50'
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
    <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6">
      <div className="flex items-center gap-2 mb-4 sm:mb-6">
        <h2 className="text-xl sm:text-2xl font-bold text-[#1A1A1A]">
          🔍 경쟁사 비교 분석
        </h2>
        <HelpTooltip content={helpContent} />
      </div>

      {/* 비교 요약 */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className={`p-4 rounded-lg ${getPositionColor(safeComparison.price_position)}`}>
          <div className="text-xs sm:text-sm text-[#4D4D4D] mb-1">가격 포지셔닝</div>
          <div className="text-lg sm:text-xl font-bold">{getPositionLabel(safeComparison.price_position)}</div>
          <div className="text-xs sm:text-sm mt-1">
            평균: {safeComparison.price_stats?.average != null ? safeComparison.price_stats.average.toLocaleString() : 'N/A'}엔
          </div>
        </div>

        <div className={`p-4 rounded-lg ${getPositionColor(safeComparison.rating_position)}`}>
          <div className="text-xs sm:text-sm text-[#4D4D4D] mb-1">평점 포지셔닝</div>
          <div className="text-lg sm:text-xl font-bold">{getPositionLabel(safeComparison.rating_position)}</div>
          <div className="text-xs sm:text-sm mt-1">
            평균: {safeComparison.rating_stats?.average != null ? safeComparison.rating_stats.average.toFixed(1) : 'N/A'}점
          </div>
        </div>

        <div className={`p-4 rounded-lg ${getPositionColor(safeComparison.review_position)}`}>
          <div className="text-xs sm:text-sm text-[#4D4D4D] mb-1">리뷰 포지셔닝</div>
          <div className="text-lg sm:text-xl font-bold">{getPositionLabel(safeComparison.review_position)}</div>
          <div className="text-xs sm:text-sm mt-1">
            평균: {safeComparison.review_stats?.average != null ? safeComparison.review_stats.average.toLocaleString() : 'N/A'}개
          </div>
        </div>
      </div>

      {/* 차별화 포인트 */}
      {differentiation_points.length > 0 && (
        <div className="mb-6">
          <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A] mb-3">
            차별화 포인트
          </h3>
          <div className="flex flex-wrap gap-2">
            {differentiation_points.map((point, idx) => (
              <span
                key={idx}
                className="px-3 py-1.5 text-xs sm:text-sm bg-blue-50 text-blue-700 rounded-lg border border-blue-200"
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
          <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A] mb-3">
            경쟁사 Top 5 비교
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#E6E6E6]">
                  <th className="text-left py-2 px-3 text-[#4D4D4D] font-medium">순위</th>
                  <th className="text-left py-2 px-3 text-[#4D4D4D] font-medium">상품명</th>
                  <th className="text-right py-2 px-3 text-[#4D4D4D] font-medium">가격</th>
                  <th className="text-right py-2 px-3 text-[#4D4D4D] font-medium">평점</th>
                  <th className="text-right py-2 px-3 text-[#4D4D4D] font-medium">리뷰</th>
                </tr>
              </thead>
              <tbody>
                {/* 타겟 상품 (강조) */}
                {target_product && (
                  <tr className="bg-blue-50 border-b border-[#E6E6E6]">
                    <td className="py-2 px-3 font-semibold text-[#0066CC]">내 상품</td>
                    <td className="py-2 px-3 font-semibold text-[#1A1A1A]">
                      {target_product.product_name || 'N/A'}
                    </td>
                    <td className="py-2 px-3 text-right font-semibold text-[#1A1A1A]">
                      {target_product.price != null ? target_product.price.toLocaleString() : 'N/A'}엔
                    </td>
                    <td className="py-2 px-3 text-right font-semibold text-[#1A1A1A]">
                      {target_product.rating != null ? target_product.rating.toFixed(1) : 'N/A'}
                    </td>
                    <td className="py-2 px-3 text-right font-semibold text-[#1A1A1A]">
                      {target_product.review_count != null ? target_product.review_count.toLocaleString() : 'N/A'}
                    </td>
                  </tr>
                )}
                {/* 경쟁사 상위 5개 */}
                {competitors.slice(0, 5).map((competitor, idx) => (
                  <tr key={competitor?.rank || idx} className="border-b border-[#E6E6E6] hover:bg-gray-50">
                    <td className="py-2 px-3 text-[#4D4D4D]">#{competitor?.rank || idx + 1}</td>
                    <td className="py-2 px-3 text-[#1A1A1A]">{competitor?.product_name || 'N/A'}</td>
                    <td className="py-2 px-3 text-right text-[#1A1A1A]">
                      {competitor?.price != null ? competitor.price.toLocaleString() : 'N/A'}엔
                    </td>
                    <td className="py-2 px-3 text-right text-[#1A1A1A]">
                      {competitor?.rating != null ? competitor.rating.toFixed(1) : 'N/A'}
                    </td>
                    <td className="py-2 px-3 text-right text-[#4D4D4D]">
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
          <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A] mb-3">
            경쟁사 분석 기반 제안
          </h3>
          <div className="space-y-3">
            {recommendations.map((rec, idx) => (
              <div key={idx} className="p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded">
                <h4 className="font-semibold text-[#1A1A1A] mb-1">{rec.title}</h4>
                <p className="text-sm text-[#4D4D4D] mb-2">{rec.description}</p>
                {rec.action_items && (
                  <ul className="text-sm text-[#1A1A1A] space-y-1">
                    {rec.action_items.map((item, i) => (
                      <li key={i} className="flex items-start">
                        <span className="text-yellow-600 mr-2">•</span>
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

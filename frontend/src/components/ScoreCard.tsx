import HelpTooltip from './HelpTooltip'
import InlineMarkdown from './InlineMarkdown'

interface ScoreCardProps {
  title: string
  score: number
  analysis: any
}

// 카드별 도움말 내용
const helpContent: Record<string, string> = {
  '이미지': '상품 이미지는 고객의 첫인상을 결정하는 중요한 요소입니다.\n\n• 썸네일 이미지는 명확하고 매력적으로 제작하세요\n• 상세 이미지는 다양한 각도와 사용 장면을 보여주세요\n• 고해상도 이미지를 사용하여 상품의 품질을 강조하세요\n• MOVE 상품 등록 시 스튜디오 촬영 지원 서비스를 활용할 수 있습니다',
  '설명': '상품 설명은 고객의 구매 결정에 큰 영향을 미칩니다.\n\n• 상품명과 검색어에 적절한 키워드를 입력하여 SEO를 향상시키세요\n• 최소 50자 이상의 상세한 설명을 작성하세요\n• 상품의 특징, 사용법, 주의사항을 명확히 설명하세요\n• 적절한 카테고리 및 브랜드 등록으로 검색 노출을 높이세요',
  '가격': '경쟁력 있는 가격 설정이 매출 증대의 핵심입니다.\n\n• 경쟁사 가격을 분석하여 적절한 가격대를 설정하세요\n• 할인율을 설정하면 고객의 관심을 끌 수 있습니다\n• 샵 쿠폰과 상품 할인을 조합하여 매출을 늘리세요\n• 메가할인/메가포 이벤트 기간에는 특별 가격 전략을 수립하세요',
  '리뷰': '고객 리뷰는 신뢰도와 전환율에 직접적인 영향을 미칩니다.\n\n• 고품질 상품과 서비스로 자연스러운 리뷰를 유도하세요\n• 샘플마켓 참여로 리뷰를 확보하고 일반 판매 페이지에도 활용하세요\n• 리뷰를 분석하여 상품 개선점을 파악하세요\n• 고객 문의에 신속하고 친절하게 대응하여 만족도를 높이세요'
}

function ScoreCard({ title, score, analysis }: ScoreCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return {
      bg: 'bg-green-600 dark:bg-green-500',
      text: 'text-green-600 dark:text-green-400',
      bgLight: 'bg-green-50 dark:bg-green-900/20',
      border: 'border-green-500 dark:border-green-400'
    }
    if (score >= 60) return {
      bg: 'bg-yellow-600 dark:bg-yellow-500',
      text: 'text-yellow-600 dark:text-yellow-400',
      bgLight: 'bg-yellow-50 dark:bg-yellow-900/20',
      border: 'border-yellow-500 dark:border-yellow-400'
    }
    return {
      bg: 'bg-red-600 dark:bg-red-500',
      text: 'text-red-600 dark:text-red-400',
      bgLight: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-500 dark:border-red-400'
    }
  }

  const getScoreLabel = (score: number) => {
    if (score >= 80) return '양호'
    if (score >= 60) return '개선 필요'
    return '긴급 개선'
  }

  const colors = getScoreColor(score)

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800/80 p-4 sm:p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-1.5 min-w-0">
          <h3 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-gray-100 truncate">{title}</h3>
          <HelpTooltip content={helpContent[title] || '이 항목에 대한 도움말입니다.'} />
        </div>
        <span className={`px-2 py-0.5 text-xs font-medium rounded ${colors.bgLight} ${colors.text}`}>
          {getScoreLabel(score)}
        </span>
      </div>
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-12 h-12 rounded-full ${colors.bg} flex items-center justify-center text-white font-bold text-lg flex-shrink-0`}>
          {score}
        </div>
        <div className="flex-1 min-w-0">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
            <div className={`h-full rounded-full ${colors.bg}`} style={{ width: `${score}%` }} />
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">{score} / 100</div>
        </div>
      </div>
      {analysis.recommendations && analysis.recommendations.length > 0 && (
        <ul className="space-y-1.5 pt-3 border-t border-gray-100 dark:border-gray-700">
          {analysis.recommendations.slice(0, 2).map((rec: string, idx: number) => (
            <li key={idx} className="text-xs sm:text-sm text-gray-700 dark:text-gray-300 leading-relaxed flex gap-1.5">
              <span className="text-blue-500 flex-shrink-0">·</span>
              <InlineMarkdown className="flex-1 min-w-0">{rec}</InlineMarkdown>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default ScoreCard

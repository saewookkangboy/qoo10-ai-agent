import HelpTooltip from './HelpTooltip'

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
      bg: 'bg-[#00AA44]',
      text: 'text-[#00AA44]',
      bgLight: 'bg-green-50',
      border: 'border-[#00AA44]'
    }
    if (score >= 60) return {
      bg: 'bg-[#FF9900]',
      text: 'text-[#FF9900]',
      bgLight: 'bg-yellow-50',
      border: 'border-[#FF9900]'
    }
    return {
      bg: 'bg-[#CC0000]',
      text: 'text-[#CC0000]',
      bgLight: 'bg-red-50',
      border: 'border-[#CC0000]'
    }
  }

  const getScoreLabel = (score: number) => {
    if (score >= 80) return '양호'
    if (score >= 60) return '개선 필요'
    return '긴급 개선'
  }

  const colors = getScoreColor(score)

  return (
    <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6 hover:shadow-[0_4px_8px_rgba(0,0,0,0.12)] transition-shadow duration-200">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <div className="flex items-center gap-2">
          <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A]">{title}</h3>
          <HelpTooltip content={helpContent[title] || '이 항목에 대한 도움말입니다.'} />
        </div>
        <span className={`px-2 sm:px-3 py-1 text-xs sm:text-sm font-medium rounded ${colors.bgLight} ${colors.text}`}>
          {getScoreLabel(score)}
        </span>
      </div>

      {/* 점수 표시 영역 */}
      <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4 mb-4 sm:mb-6">
        {/* 큰 점수 원형 표시 */}
        <div className={`w-20 h-20 sm:w-24 sm:h-24 rounded-full ${colors.bg} flex items-center justify-center text-white font-bold text-2xl sm:text-3xl flex-shrink-0`}>
          {score}
        </div>
        
        {/* 진행 바 및 세부 정보 */}
        <div className="flex-1 w-full sm:w-auto">
          <div className="w-full bg-[#E6E6E6] rounded-full h-2 sm:h-2.5 mb-3">
            <div
              className={`h-full rounded-full ${colors.bg} transition-all duration-500`}
              style={{ width: `${score}%` }}
            ></div>
          </div>
          <div className="text-xs sm:text-sm text-[#4D4D4D]">
            <span className="font-medium">{score}점</span>
            <span className="mx-1">/</span>
            <span>100점</span>
          </div>
        </div>
      </div>

      {/* 주요 제안 */}
      {analysis.recommendations && analysis.recommendations.length > 0 && (
        <div className="mt-4 sm:mt-6 pt-4 sm:pt-6 border-t border-[#E6E6E6]">
          <p className="text-xs sm:text-sm font-medium text-[#4D4D4D] mb-2 sm:mb-3">주요 제안</p>
          <ul className="space-y-1.5 sm:space-y-2">
            {analysis.recommendations.slice(0, 2).map((rec: string, idx: number) => (
              <li key={idx} className="flex items-start text-xs sm:text-sm text-[#1A1A1A]">
                <span className="text-[#0066CC] mr-2 mt-0.5 flex-shrink-0">•</span>
                <span className="leading-relaxed">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default ScoreCard

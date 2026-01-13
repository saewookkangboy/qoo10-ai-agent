import { useState, useMemo } from 'react'

// 메뉴얼 데이터 (Qoo10 큐텐 대학 한국어 메뉴얼 기반)
const manualData = [
  {
    category: '입점 검토하기',
    title: 'Qoo10 Japan의 판매 수수료는 얼마일까요?',
    content: 'Qoo10 Japan에서는 입점 시 초기 비용과 월 고정비용은 전액 무료입니다. 판매 수수료는 상품 카테고리에 따라 6%~10%이며, 추가 수수료와 출금 수수료가 발생할 수 있습니다.',
    keywords: ['수수료', '입점', '비용', '정산', '출금']
  },
  {
    category: '판매 준비하기',
    title: '지금 바로 실천할 수 있는 매출 상승을 위한 10가지 전략',
    content: '상품 페이지 최적화, 검색 키워드 최적화, 가격 전략 수립, 고객 리뷰 관리, 프로모션 활용, 광고 전략 수립 등을 통해 매출을 향상시킬 수 있습니다.',
    keywords: ['매출', '전략', '최적화', '키워드', '프로모션']
  },
  {
    category: '판매 준비하기',
    title: 'MOVE 상품 등록하는 방법 총정리!',
    content: 'MOVE 상품 등록의 전체 프로세스를 단계별로 안내합니다. 상품 정보 입력, 이미지 등록, 가격 설정, 배송 정보 설정, Cafe24 연동 방법 등을 포함합니다.',
    keywords: ['MOVE', '상품 등록', '이미지', '가격', '배송']
  },
  {
    category: '판매 준비하기',
    title: 'JQSM(판매 관리 툴) 용어 모음',
    content: 'JQSM은 Qoo10 Japan Sales Manager로 판매자를 위한 관리 도구입니다. 주문 관리, 상품 관리, 정산 관리, 문의/기타 기능을 제공합니다.',
    keywords: ['JQSM', '관리', '주문', '정산', '문의']
  },
  {
    category: '주문・배송・고객 관리하기',
    title: '고객 클레임을 최소화하는 취소 처리 대응 방법',
    content: '취소 요청을 효율적으로 처리하고 고객 불만을 최소화하는 방법을 제시합니다. 취소 사유별 대응 방법, 환불 처리 프로세스, 고객 만족도 유지를 위한 커뮤니케이션 방법을 포함합니다.',
    keywords: ['취소', '클레임', '환불', '고객', '대응']
  },
  {
    category: '주문・배송・고객 관리하기',
    title: '일본 해외배송을 효율적으로 시작하는 방법',
    content: '해외 배송의 기본 절차와 효율적인 운영 방법을 안내합니다. 통관 서류 준비, 배송비 계산 및 설정, 배송 추적 시스템 구축, 배송 지연 시 대응 방법을 포함합니다.',
    keywords: ['배송', '해외', '통관', '배송비', '추적']
  },
  {
    category: '판매 데이터 관리・분석하기',
    title: '놓치기 쉬운 판매 데이터 분석 및 활용 방법',
    content: 'Qoo10 Analytics를 활용하여 검색 키워드 분석, 유입 경로 분석, 전환율 분석, SEO 대책, 히트상품 발굴을 할 수 있습니다.',
    keywords: ['데이터', '분석', 'Analytics', '키워드', 'SEO', '전환율']
  },
  {
    category: '판매 데이터 관리・분석하기',
    title: '히트상품을 만드는 「시장 분석 방법 3가지」',
    content: '경쟁사 분석 방법, 트렌드 분석 및 예측, 고객 니즈 분석을 통해 히트 상품을 만드는 방법을 소개합니다.',
    keywords: ['히트상품', '시장 분석', '경쟁사', '트렌드', '고객']
  },
  {
    category: '매출 증대시키기',
    title: '매출 증대를 위한 샘플마켓 참가 가이드',
    content: '샘플마켓에 참가하기 위해서는 상품 수량이 10개 이상이어야 합니다. 참가 신청서를 작성 후 제출하면, 심사를 거쳐 참가 여부가 결정됩니다. 샘플마켓 리뷰를 일반 판매 페이지에도 활용할 수 있습니다.',
    keywords: ['샘플마켓', '매출', '리뷰', '참가', '프로모션']
  },
  {
    category: '매출 증대시키기',
    title: '고객을 사로잡는 입구 상품을 만드는 방법',
    content: '고객의 관심을 끌고 구매로 이어지게 하는 입구 상품 구성 방법을 제시합니다. 입구 상품 선정 기준, 가격 전략 수립, 상품 페이지 구성 방법, 고객 유입 전환 전략을 포함합니다.',
    keywords: ['입구 상품', '고객', '전환', '가격', '페이지']
  },
  {
    category: '광고・프로모션 활용하기',
    title: '2025년 최신! Qoo10 Japan 광고・프로모션 총정리',
    content: '파워랭크업(검색형 광고), 스마트세일즈(알고리즘 기반 광고), 플러스 전시(전시형 광고), 키워드 플러스 등 다양한 광고 옵션과 샵 쿠폰, 상품 할인, 샘플마켓, 메가할인/메가포 이벤트 등 프로모션을 활용할 수 있습니다.',
    keywords: ['광고', '프로모션', '파워랭크업', '스마트세일즈', '쿠폰', '할인']
  },
  {
    category: '광고・프로모션 활용하기',
    title: '알고리즘이 최적의 위치에 상품을 노출하는 스마트세일즈',
    content: '스마트세일즈 기능의 작동 원리와 활용 방법을 안내합니다. 상품 최적화 방법, 예산 설정 및 관리, 성과 측정 및 개선 방법을 포함합니다.',
    keywords: ['스마트세일즈', '알고리즘', '노출', '최적화', '예산']
  },
  {
    category: '메가할인・메가포 대비하기',
    title: '메가할인 정산 완벽 가이드! 선차감과 환급 과정 이해하기',
    content: '메가할인 이벤트의 정산 구조, 선차감과 환급 프로세스를 상세히 설명합니다. 정산금 계산 방법, 정산 관련 주의사항, 정산 이의제기 및 문의 방법을 포함합니다.',
    keywords: ['메가할인', '정산', '선차감', '환급', '이벤트']
  },
  {
    category: '메가할인・메가포 대비하기',
    title: '메가포 환원포인트를 활용하고 재방문 고객을 늘리세요',
    content: '메가포의 환원포인트 시스템을 활용하여 고객 재방문을 유도하는 방법을 설명합니다. 환원포인트 활용 전략, 재방문 고객 유도 방법, 재구매율 향상 전략을 포함합니다.',
    keywords: ['메가포', '환원포인트', '재방문', '고객', '재구매']
  },
  {
    category: '단계별 교육 (초급)',
    title: '초보 셀러를 위한 단계별 교육',
    content: '초보 판매자를 위한 기본 개념, 플랫폼 이용법, 상품 등록 등 기초부터 차근차근 배우는 맞춤형 교육 과정입니다. 총 8개의 단계별 교육 과정이 동영상으로 제공됩니다.',
    keywords: ['초보', '교육', '기초', '단계별', '동영상']
  }
]

interface ManualSearchProps {
  onClose?: () => void
}

function ManualSearch({ onClose }: ManualSearchProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('전체')

  // 카테고리 목록 추출
  const categories = useMemo(() => {
    const uniqueCategories = Array.from(new Set(manualData.map(item => item.category)))
    return ['전체', ...uniqueCategories]
  }, [])

  // 검색 결과 필터링
  const filteredResults = useMemo(() => {
    let results = manualData

    // 카테고리 필터
    if (selectedCategory !== '전체') {
      results = results.filter(item => item.category === selectedCategory)
    }

    // 검색어 필터
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      results = results.filter(item => {
        const titleMatch = item.title.toLowerCase().includes(query)
        const contentMatch = item.content.toLowerCase().includes(query)
        const keywordMatch = item.keywords.some(keyword => keyword.toLowerCase().includes(query))
        return titleMatch || contentMatch || keywordMatch
      })
    }

    return results
  }, [searchQuery, selectedCategory])

  return (
    <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6">
      <div className="flex items-center justify-between mb-4 sm:mb-6">
        <h2 className="text-xl sm:text-2xl font-bold text-[#1A1A1A]">
          📚 Qoo10 큐텐 대학 메뉴얼 검색
        </h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl"
            aria-label="닫기"
          >
            ×
          </button>
        )}
      </div>

      {/* 검색 바 */}
      <div className="mb-4 sm:mb-6">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="검색어를 입력하세요 (예: 수수료, 광고, 배송, 매출 등)"
            className="w-full px-4 py-3 pr-10 border border-[#E6E6E6] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0066CC] focus:border-transparent text-sm sm:text-base"
          />
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
        </div>
      </div>

      {/* 카테고리 필터 */}
      <div className="mb-4 sm:mb-6">
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-3 py-1.5 text-xs sm:text-sm font-medium rounded-lg transition-colors ${
                selectedCategory === category
                  ? 'bg-[#0066CC] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* 검색 결과 */}
      <div className="space-y-3 sm:space-y-4 max-h-96 overflow-y-auto">
        {filteredResults.length > 0 ? (
          filteredResults.map((item, index) => (
            <div
              key={index}
              className="border border-[#E6E6E6] rounded-lg p-3 sm:p-4 hover:shadow-[0_2px_4px_rgba(0,0,0,0.08)] transition-shadow"
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex-1">
                  <span className="inline-block px-2 py-0.5 text-xs bg-blue-50 text-blue-700 rounded mb-2">
                    {item.category}
                  </span>
                  <h3 className="text-sm sm:text-base font-semibold text-[#1A1A1A] mb-2">
                    {item.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-[#4D4D4D] leading-relaxed">
                    {item.content}
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap gap-1 mt-2">
                {item.keywords.slice(0, 5).map((keyword, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                  >
                    #{keyword}
                  </span>
                ))}
              </div>
            </div>
          ))
        ) : (
          <div className="text-center py-8 sm:py-12">
            <p className="text-sm sm:text-base text-[#4D4D4D]">
              검색 결과가 없습니다. 다른 검색어를 시도해보세요.
            </p>
          </div>
        )}
      </div>

      {/* 결과 개수 */}
      {searchQuery && (
        <div className="mt-4 pt-4 border-t border-[#E6E6E6] text-xs sm:text-sm text-[#4D4D4D]">
          총 {filteredResults.length}개의 결과를 찾았습니다.
        </div>
      )}
    </div>
  )
}

export default ManualSearch

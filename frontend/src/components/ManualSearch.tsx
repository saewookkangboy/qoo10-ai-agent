import { useState, useMemo } from 'react'

// 메뉴얼 데이터 타입 정의
interface ManualItem {
  category: string
  title: string
  content: string
  keywords: string[]
  details?: string[]
  tips?: string[]
  relatedItems?: string[]
  link?: string
  checklist?: string[]
}

// 메뉴얼 데이터 (Qoo10 큐텐 대학 한국어 메뉴얼 기반)
const manualData: ManualItem[] = [
  {
    category: '입점 검토하기',
    title: 'Qoo10 Japan의 판매 수수료는 얼마일까요?',
    content: 'Qoo10 Japan에서는 입점 시 초기 비용과 월 고정비용은 전액 무료입니다. 판매 수수료는 상품 카테고리에 따라 6%~10%이며, 추가 수수료와 출금 수수료가 발생할 수 있습니다.',
    keywords: ['수수료', '입점', '비용', '정산', '출금'],
    details: [
      '초기 비용 및 월 비용은 완전 무료입니다',
      '판매 수수료: 상품 카테고리에 따라 6%~10%',
      '추가 수수료: 예약주문 +2%, 해외계좌/배송지 +2%, 외부광고 +1%',
      '출금 수수료: 회당 150엔 (판매 금액/수량과 무관)',
      '카테고리별 수수료: 여성패션/뷰티 10%, 남성/스포츠 6~10%, 가전/PC 8~10% 등'
    ],
    tips: [
      '라쿠텐 마켓이나 아마존과 달리 초기 비용이 없어 위험 부담 없이 시작 가능',
      '샵 레벨이 높을수록 정산 리드타임이 짧아집니다 (일반: 15일, 우수: 10일, 파워: 5일)',
      'Q지갑에 입금된 정산금은 언제든지 출금 가능하지만, 출금 수수료를 고려하여 출금 빈도를 조절하세요'
    ],
    relatedItems: ['판매자 입점에 대한 모든 것 1탄', '판매자 입점에 대한 모든 것 2탄'],
    link: 'https://article-university.qoo10.jp/entry/130',
    checklist: [
      '상품 카테고리별 수수료 확인',
      '추가 수수료 발생 조건 확인',
      '정산 시기 및 출금 방법 이해',
      '샵 레벨 향상 전략 수립'
    ]
  },
  {
    category: '판매 준비하기',
    title: '지금 바로 실천할 수 있는 매출 상승을 위한 10가지 전략',
    content: '상품 페이지 최적화, 검색 키워드 최적화, 가격 전략 수립, 고객 리뷰 관리, 프로모션 활용, 광고 전략 수립 등을 통해 매출을 향상시킬 수 있습니다.',
    keywords: ['매출', '전략', '최적화', '키워드', '프로모션'],
    details: [
      '상품 페이지 최적화: 명확한 상품명, 상세한 설명, 고품질 이미지',
      '검색 키워드 최적화: 인기 키워드 분석 및 상품명/검색어에 반영',
      '가격 전략 수립: 경쟁사 분석 기반 경쟁력 있는 가격 설정',
      '고객 리뷰 관리: 리뷰 분석 및 개선점 파악, 고객 문의 신속 대응',
      '프로모션 활용: 샵 쿠폰, 상품 할인, 샘플마켓 등 다양한 프로모션',
      '광고 전략 수립: 파워랭크업, 스마트세일즈, 플러스 전시 등 광고 활용',
      '배송 옵션 다양화: 무료배송, 빠른 배송 등 고객 편의성 제공',
      '고객 서비스 개선: 신속한 문의 대응, 친절한 커뮤니케이션',
      '데이터 분석 기반 의사결정: Qoo10 Analytics 활용',
      '지속적인 개선 및 테스트: A/B 테스트를 통한 최적화'
    ],
    tips: [
      '즉시 적용 가능한 전략부터 시작하여 단계적으로 개선하세요',
      '데이터를 기반으로 의사결정을 내리면 효과가 더 큽니다',
      '고객 피드백을 적극적으로 수집하고 반영하세요'
    ],
    relatedItems: ['Qoo10 Analytics 활용법', '경쟁사 분석 방법'],
    link: 'https://article-university.qoo10.jp/qoo10-selling-tips_kor#판매-준비하기'
  },
  {
    category: '판매 준비하기',
    title: 'MOVE 상품 등록하는 방법 총정리!',
    content: 'MOVE 상품 등록의 전체 프로세스를 단계별로 안내합니다. 상품 정보 입력, 이미지 등록, 가격 설정, 배송 정보 설정, Cafe24 연동 방법 등을 포함합니다.',
    keywords: ['MOVE', '상품 등록', '이미지', '가격', '배송'],
    details: [
      'MOVE 상품이란 무엇인가?',
      'MOVE 상품 등록 절차 및 단계별 가이드',
      '상품 정보 입력 방법 (상품명, 설명, 카테고리 등)',
      '이미지 등록 가이드라인 (썸네일, 상세 이미지)',
      '가격 설정 방법 (판매가, 할인율 등)',
      '배송 정보 설정 (배송비, 배송 방법)',
      '등록 후 관리 방법',
      'Cafe24 연동 방법',
      '스튜디오 촬영 지원 서비스 활용'
    ],
    tips: [
      'MOVE 상품은 추가 노출 기회를 제공합니다',
      '스튜디오 촬영 지원 서비스를 활용하면 전문적인 상품 이미지를 확보할 수 있습니다',
      'Cafe24 연동 시 자동으로 상품 정보가 동기화됩니다'
    ],
    relatedItems: ['상품 페이지 최적화', '이미지 등록 가이드라인'],
    link: 'https://article-university.qoo10.jp/qoo10-selling-tips_kor#판매-준비하기',
    checklist: [
      'MOVE 상품 등록 조건 확인',
      '상품 정보 입력 완료',
      '이미지 등록 (최소 3장 이상 권장)',
      '가격 및 배송 정보 설정',
      'Cafe24 연동 (해당 시)'
    ]
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
    keywords: ['데이터', '분석', 'Analytics', '키워드', 'SEO', '전환율'],
    details: [
      '검색 키워드 분석: 인기 키워드를 파악하여 상품명과 검색어에 반영',
      '유입 경로 분석: 고객이 어떤 경로로 상품 페이지에 도달하는지 분석',
      '전환율 분석: 상품별 전환율을 분석하여 개선이 필요한 상품 파악',
      'SEO 대책: 상품명, 검색어, 카테고리, 브랜드 등록으로 검색 노출 향상',
      '히트상품 발굴: 매출 상승으로 이어질 새로운 히트상품의 새싹 찾기'
    ],
    tips: [
      'SEO에서 중요한 것은 사용자가 검색하는 키워드를 파악하는 것입니다',
      '인기 키워드를 상품명과 검색어에 적절히 입력하면 검색 노출이 향상됩니다',
      '유입 경로별 전환율을 확인하여 효과적인 마케팅 채널을 파악하세요',
      '전환율이 낮은 상품은 상품 페이지 개선이나 가격 조정을 고려하세요',
      '플러스 전시, 파워랭크업, 스마트 세일즈 광고를 활용하면 SEO 효과를 높일 수 있습니다'
    ],
    relatedItems: ['히트상품을 만드는 시장 분석 방법 3가지', 'JQSM·Qoo10 Analytics 활용법'],
    link: 'https://article-university.qoo10.jp/entry/107',
    checklist: [
      'Qoo10 Analytics 접속 및 기본 기능 파악',
      '검색 키워드 분석 실시',
      '유입 경로 분석 및 전환율 확인',
      'SEO 최적화 작업 (상품명, 검색어, 카테고리)',
      '히트상품 후보 발굴 및 개선'
    ]
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
    keywords: ['샘플마켓', '매출', '리뷰', '참가', '프로모션'],
    details: [
      '참가 조건: 상품 수량 10개 이상 (상품 종류/카테고리 제한 없음)',
      '참가 빈도: 한 달에 두 번 진행',
      '참가 예약: 3개월 전부터 예약이 완료될 정도로 인기 있는 이벤트',
      '신청서 작성 항목: 이미지, Seller ID, SHOP PAGE, 브랜드명, 상품번호, 샘플마켓용 상품번호, 상품명, 상품 유형, 제공 수량, 개당 비용, 총 비용',
      '참가 후 절차: Qoo10 Japan 담당자와 재고, 비용, 모바일/PC 배너 등 협의'
    ],
    tips: [
      '샘플마켓 참여 상품에 대한 리뷰를 일반 판매 페이지에도 활용하여 전환율 향상',
      '샘플마켓 리뷰를 활용해 상품을 개선하고 홍보 활동에 활용',
      '사전 준비가 중요하므로 참여 상품 선정, 혜택 제공, 리뷰 활용 전략을 미리 수립하세요',
      '샘플마켓은 단골 고객을 만들고 매출을 향상시키는 매우 효과적인 프로모션입니다'
    ],
    relatedItems: ['고객을 사로잡는 입구 상품을 만드는 방법', '리뷰 관리'],
    link: 'https://article-university.qoo10.jp/entry/157',
    checklist: [
      '상품 수량 10개 이상 확인',
      '신청서 작성 및 제출',
      '참가 확정 대기',
      '담당자와 협의 (재고, 비용, 배너)',
      '리뷰 활용 전략 수립'
    ]
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
    keywords: ['광고', '프로모션', '파워랭크업', '스마트세일즈', '쿠폰', '할인'],
    details: [
      '파워랭크업: 200엔부터 사용할 수 있는 검색형 광고',
      '스마트세일즈: 알고리즘이 최적의 위치에 상품을 노출하는 광고',
      '플러스 전시: 상품 노출을 높이는 전시형 광고',
      '키워드 플러스: 특정 키워드 검색 시 상품 노출',
      '샵 쿠폰: 고객에게 할인 혜택을 제공하는 쿠폰',
      '상품 할인: 상품 가격 할인 프로모션',
      '샘플마켓: 리뷰 확보 및 홍보를 위한 샘플 제공 이벤트',
      '메가할인/메가포: Qoo10의 최대 쇼핑 축제 이벤트'
    ],
    tips: [
      '할인과 광고를 조합하면 ROAS(광고 투자 대비 수익)를 향상시킬 수 있습니다',
      '초보자는 파워랭크업부터 시작하여 점진적으로 광고 예산을 늘리는 것을 권장합니다',
      '스마트세일즈는 알고리즘이 자동으로 최적화하므로 초보자에게 적합합니다',
      '메가할인/메가포 기간에는 광고 예산을 늘려 매출을 극대화하세요'
    ],
    relatedItems: ['스마트세일즈 활용법', '메가할인 기간 매출 극대화 전략'],
    link: 'https://article-university.qoo10.jp/qoo10-selling-tips_kor#광고-프로모션-활용하기',
    checklist: [
      '광고 목표 및 예산 설정',
      '적합한 광고 유형 선택 (파워랭크업, 스마트세일즈 등)',
      '키워드 및 타겟팅 설정',
      '프로모션 조합 (할인 + 광고)',
      '성과 측정 및 최적화'
    ]
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
  const [selectedItem, setSelectedItem] = useState<ManualItem | null>(null)

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
              onClick={() => setSelectedItem(item)}
              className="border border-[#E6E6E6] rounded-lg p-3 sm:p-4 hover:shadow-[0_2px_4px_rgba(0,0,0,0.08)] transition-shadow cursor-pointer"
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
              <div className="flex items-center justify-between mt-2">
                <div className="flex flex-wrap gap-1">
                  {item.keywords.slice(0, 5).map((keyword, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                    >
                      #{keyword}
                    </span>
                  ))}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedItem(item)
                  }}
                  className="text-xs sm:text-sm text-[#0066CC] hover:text-[#004499] font-medium ml-2"
                >
                  상세보기 →
                </button>
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

      {/* 상세 모달 */}
      {selectedItem && (
        <ManualDetailModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onRelatedClick={(title) => {
            const relatedItem = manualData.find(item => item.title.includes(title))
            if (relatedItem) {
              setSelectedItem(relatedItem)
            }
          }}
        />
      )}

      {/* 결과 개수 */}
      {searchQuery && (
        <div className="mt-4 pt-4 border-t border-[#E6E6E6] text-xs sm:text-sm text-[#4D4D4D]">
          총 {filteredResults.length}개의 결과를 찾았습니다.
        </div>
      )}
    </div>
  )
}

// 상세 모달 컴포넌트
interface ManualDetailModalProps {
  item: ManualItem
  onClose: () => void
  onRelatedClick: (title: string) => void
}

function ManualDetailModal({ item, onRelatedClick, onClose }: ManualDetailModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 헤더 */}
        <div className="sticky top-0 bg-white border-b border-[#E6E6E6] p-4 sm:p-6 flex items-center justify-between">
          <div className="flex-1">
            <span className="inline-block px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded mb-2">
              {item.category}
            </span>
            <h2 className="text-xl sm:text-2xl font-bold text-[#1A1A1A]">
              {item.title}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="ml-4 text-gray-400 hover:text-gray-600 text-2xl font-bold"
            aria-label="닫기"
          >
            ×
          </button>
        </div>

        {/* 내용 */}
        <div className="p-4 sm:p-6 space-y-6">
          {/* 개요 */}
          <div>
            <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A] mb-2">
              📋 개요
            </h3>
            <p className="text-sm sm:text-base text-[#4D4D4D] leading-relaxed">
              {item.content}
            </p>
          </div>

          {/* 상세 내용 */}
          {item.details && item.details.length > 0 && (
            <div>
              <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A] mb-3">
                📝 상세 내용
              </h3>
              <ul className="space-y-2">
                {item.details.map((detail, idx) => (
                  <li key={idx} className="flex items-start text-sm sm:text-base text-[#4D4D4D]">
                    <span className="text-[#0066CC] mr-2 mt-1 flex-shrink-0">•</span>
                    <span className="leading-relaxed">{detail}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 실전 팁 */}
          {item.tips && item.tips.length > 0 && (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
              <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A] mb-3">
                💡 실전 팁
              </h3>
              <ul className="space-y-2">
                {item.tips.map((tip, idx) => (
                  <li key={idx} className="flex items-start text-sm sm:text-base text-[#4D4D4D]">
                    <span className="text-yellow-600 mr-2 mt-1 flex-shrink-0">✓</span>
                    <span className="leading-relaxed">{tip}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 체크리스트 */}
          {item.checklist && item.checklist.length > 0 && (
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
              <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A] mb-3">
                ✅ 체크리스트
              </h3>
              <ul className="space-y-2">
                {item.checklist.map((check, idx) => (
                  <li key={idx} className="flex items-start text-sm sm:text-base text-[#4D4D4D]">
                    <span className="text-blue-600 mr-2 mt-1 flex-shrink-0">□</span>
                    <span className="leading-relaxed">{check}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* 관련 항목 */}
          {item.relatedItems && item.relatedItems.length > 0 && (
            <div>
              <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A] mb-3">
                🔗 관련 항목
              </h3>
              <div className="flex flex-wrap gap-2">
                {item.relatedItems.map((related, idx) => (
                  <button
                    key={idx}
                    onClick={() => onRelatedClick(related)}
                    className="px-3 py-1.5 text-xs sm:text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    {related}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* 키워드 */}
          <div>
            <h3 className="text-base sm:text-lg font-semibold text-[#1A1A1A] mb-3">
              🏷️ 관련 키워드
            </h3>
            <div className="flex flex-wrap gap-2">
              {item.keywords.map((keyword, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1.5 text-xs sm:text-sm bg-gray-100 text-gray-600 rounded-lg"
                >
                  #{keyword}
                </span>
              ))}
            </div>
          </div>

          {/* 링크 */}
          {item.link && (
            <div className="pt-4 border-t border-[#E6E6E6]">
              <a
                href={item.link}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm sm:text-base text-[#0066CC] hover:text-[#004499] font-medium"
              >
                <span className="mr-2">🔗</span>
                큐텐 대학에서 더 자세히 보기
                <span className="ml-2">→</span>
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ManualSearch

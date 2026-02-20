import { ChecklistResult, ShopData } from '../types'
import HelpTooltip from './HelpTooltip'
import ErrorReportButton from './ErrorReportButton'

interface ChecklistCardProps {
  checklist: ChecklistResult
  analysisId?: string
  productData?: any
  shopData?: ShopData
}

const helpContent = '이 체크리스트는 Qoo10 큐텐 대학의 판매 준비 가이드를 기반으로 합니다.\n\n• 상품 등록: 상품명, 설명, 이미지 등 필수 정보를 확인합니다\n• 가격 설정: 판매가, 할인율, 쿠폰 할인 등을 점검합니다\n• 배송 정보: 배송비, 배송 방법, 통관 정보를 확인합니다\n• 프로모션: 샵 쿠폰, 상품 할인, 광고 활용 여부를 점검합니다\n\n완성도가 높을수록 검색 노출과 전환율이 향상됩니다.'

function ChecklistCard({ checklist, analysisId, productData, shopData }: ChecklistCardProps) {
  const overallCompletion = checklist.overall_completion

  const getCompletionColor = (rate: number) => {
    if (rate >= 80) {
      return {
        text: 'text-green-600 dark:text-green-400',
        bg: 'bg-green-50 dark:bg-green-900/20',
        border: 'border-green-500 dark:border-green-400',
        badge: 'bg-green-600 dark:bg-green-500 text-white'
      }
    }
    if (rate >= 60) {
      return {
        text: 'text-yellow-600 dark:text-yellow-400',
        bg: 'bg-yellow-50 dark:bg-yellow-900/20',
        border: 'border-yellow-500 dark:border-yellow-400',
        badge: 'bg-yellow-600 dark:bg-yellow-500 text-white'
      }
    }
    return {
      text: 'text-red-600 dark:text-red-400',
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-500 dark:border-red-400',
      badge: 'bg-red-600 dark:bg-red-500 text-white'
    }
  }

  const overallColors = getCompletionColor(overallCompletion)

  // Shop 데이터에서 필드 값을 가져오는 헬퍼 함수
  const _getFieldValueFromShopData = (itemId: string, shopData: ShopData | undefined): any => {
    if (!shopData) return undefined
    
    const fieldMapping: Record<string, string> = {
      'item_001': 'shop_name',
      'item_002': 'shop_level',
      'item_003': 'follower_count',
      'item_004': 'product_count',
      'item_005': 'categories',
      'item_006': 'coupons',
    }
    
    const fieldPath = fieldMapping[itemId]
    if (!fieldPath) return undefined
    
    // 간단한 필드 접근 (중첩 필드는 나중에 확장 가능)
    return (shopData as any)[fieldPath]
  }

  // 체크리스트 항목 ID를 필드명으로 매핑하는 헬퍼 함수
  const _getFieldValueFromProductData = (itemId: string, productData: any): any => {
    // 체크리스트 항목 ID를 실제 데이터 필드로 매핑
    const fieldMapping: Record<string, string> = {
      'item_001': 'product_name',
      'item_002': 'description',
      'item_003': 'images',
      'item_004': 'price.sale_price',
      'item_005': 'price.original_price',
      'item_006a': 'qpoint_info.max_points',
      'item_006b': 'qpoint_info',
      'item_007': 'shipping_info.shipping_fee',
      'item_008': 'shipping_info.free_shipping',
      'item_009': 'shipping_info.return_policy',
      'item_010': 'reviews.review_count',
      'item_011': 'coupon_info.has_coupon',
      'item_012': 'coupon_info',
      'item_013': 'seller_info.shop_name',
      'item_014': 'seller_info.follower_count',
      'item_015': 'seller_info.shop_level',
      'item_016': 'seller_info.product_count',
      'item_017': 'category',
      'item_018': 'brand',
      'item_019': 'search_keywords',
      'item_020': 'coupon_info.shop_coupon',
      'item_021': 'coupon_info.product_discount',
      'item_022': 'coupon_info.promotion',
    }
    
    const fieldPath = fieldMapping[itemId]
    if (!fieldPath || !productData) return undefined
    
    // 중첩된 필드 접근 (예: 'price.sale_price')
    const parts = fieldPath.split('.')
    let value = productData
    for (const part of parts) {
      if (value && typeof value === 'object' && part in value) {
        value = value[part]
      } else {
        return undefined
      }
    }
    
    return value
  }

  return (
    <div className="space-y-6">
      <div className={`rounded-xl border-2 ${overallColors.border} ${overallColors.bg} p-4 sm:p-5`}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">메뉴얼 기반 체크리스트</h2>
            <HelpTooltip content={helpContent} />
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-2xl font-bold ${overallColors.text}`}>{overallCompletion}%</span>
            <span className={`px-3 py-1 rounded-lg text-sm font-semibold ${overallColors.badge}`}>
              {overallCompletion >= 80 ? '양호' : overallCompletion >= 60 ? '개선 필요' : '긴급 개선'}
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {checklist.checklists.map((category, idx) => {
          const categoryColors = getCompletionColor(category.completion_rate)
          return (
            <div key={idx} className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800/80 p-4 sm:p-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-4 mb-4 border-b border-gray-200 dark:border-gray-600">
                <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100">{category.category}</h3>
                <div className="flex items-center gap-2">
                  <span className={`text-lg font-bold ${categoryColors.text}`}>{category.completion_rate}%</span>
                  <span className={`px-2 py-0.5 text-xs font-semibold rounded ${categoryColors.badge}`}>
                    {category.completion_rate >= 80 ? '완료' : category.completion_rate >= 60 ? '진행중' : '미완료'}
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                {category.items.map((item) => {
                  const isCompleted = item.status === 'completed'
                  return (
                    <div
                      key={item.id}
                      className={`rounded-xl border p-4 ${
                        isCompleted
                          ? 'border-green-200 dark:border-green-800 bg-green-50/50 dark:bg-green-900/20 border-l-4 border-l-green-500'
                          : 'border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50 border-l-4 border-l-gray-300 dark:border-l-gray-600'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-0.5">
                          {isCompleted ? (
                            <div className="w-5 h-5 rounded-full bg-green-500 dark:bg-green-400 flex items-center justify-center text-white text-xs font-bold">✓</div>
                          ) : (
                            <div className="w-5 h-5 rounded-full border-2 border-gray-300 dark:border-gray-600" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <h4 className={`text-sm font-semibold ${isCompleted ? 'text-gray-900 dark:text-gray-100' : 'text-gray-700 dark:text-gray-300'}`}>
                              {item.title}
                            </h4>
                            {item.auto_checked && (
                              <span className="px-1.5 py-0.5 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded">자동</span>
                            )}
                          </div>
                          <p className={`text-xs leading-relaxed ${isCompleted ? 'text-gray-600 dark:text-gray-400' : 'text-gray-500 dark:text-gray-500'}`}>
                            {item.description}
                          </p>
                          {item.recommendation && (
                            <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                              <p className="text-xs font-medium text-amber-700 dark:text-amber-300 mb-0.5">개선 제안</p>
                              <p className="text-xs text-gray-700 dark:text-gray-300">{item.recommendation}</p>
                            </div>
                          )}
                          {analysisId && (
                            <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 flex items-center justify-between">
                              <span className="text-xs text-gray-500 dark:text-gray-400">결과가 다르다면</span>
                              <ErrorReportButton
                                analysisId={analysisId}
                                fieldName={item.id}
                                crawlerValue={
                                  productData ? _getFieldValueFromProductData(item.id, productData) : shopData ? _getFieldValueFromShopData(item.id, shopData) : undefined
                                }
                                reportValue={item.status === 'completed' ? 'completed' : 'pending'}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ChecklistCard

export interface AnalyzeRequest {
  url: string
  url_type?: string
}

export interface AnalyzeResponse {
  analysis_id: string
  status: string
  url_type: string
  estimated_time: number
}

export interface AnalysisResult {
  analysis_id: string
  status: 'processing' | 'completed' | 'failed'
  result?: {
    product_analysis?: ProductAnalysis
    shop_analysis?: any
    recommendations: Recommendation[]
    checklist?: ChecklistResult
    competitor_analysis?: CompetitorAnalysis
    product_data?: ProductData
    shop_data?: any
  }
  error?: string
}

export interface ChecklistResult {
  overall_completion: number
  checklists: ChecklistCategory[]
}

export interface ChecklistCategory {
  category: string
  completion_rate: number
  items: ChecklistItem[]
}

export interface ChecklistItem {
  id: string
  title: string
  description: string
  status: 'completed' | 'pending'
  auto_checked: boolean
  recommendation?: string
}

export interface CompetitorAnalysis {
  target_product: {
    product_name: string
    price: number | null
    rating: number
    review_count: number
  }
  competitors: Competitor[]
  comparison: ComparisonResult
  differentiation_points: string[]
  recommendations: Recommendation[]
}

export interface Competitor {
  rank: number
  product_name: string
  price: number
  rating: number
  review_count: number
  discount_rate: number
  has_coupon: boolean
  advertising: string[]
}

export interface ComparisonResult {
  price_position: string
  price_stats: {
    target: number
    average: number
    min: number
    max: number
  }
  rating_position: string
  rating_stats: {
    target: number
    average: number
  }
  review_position: string
  review_stats: {
    target: number
    average: number
  }
}

export interface ProductAnalysis {
  overall_score: number
  image_analysis: ImageAnalysis
  description_analysis: DescriptionAnalysis
  price_analysis: PriceAnalysis
  review_analysis: ReviewAnalysis
  seo_analysis: SEOAnalysis
}

export interface ImageAnalysis {
  score: number
  thumbnail_quality: string
  image_count: number
  recommendations: string[]
}

export interface DescriptionAnalysis {
  score: number
  description_length: number
  seo_keywords: string[]
  structure_quality: string
  recommendations: string[]
}

export interface PriceAnalysis {
  score: number
  sale_price: number | null
  original_price: number | null
  discount_rate: number
  positioning: string
  recommendations: string[]
}

export interface ReviewAnalysis {
  score: number
  rating: number
  review_count: number
  negative_ratio: number
  recommendations: string[]
}

export interface SEOAnalysis {
  score: number
  keywords_in_name: boolean
  keywords_in_description: boolean
  category_set: boolean
  brand_set: boolean
  recommendations: string[]
}

export interface Recommendation {
  id: string
  category: string
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  action_items: string[]
  expected_impact: string
  difficulty: string
  estimated_time: string
  manual_reference: string
}

export interface ProductData {
  url: string
  product_code: string | null
  product_name: string
  category: string | null
  brand: string | null
  price: {
    original_price: number | null
    sale_price: number | null
    discount_rate: number
  }
  images: {
    thumbnail: string | null
    detail_images: string[]
  }
  description: string
  search_keywords: string[]
  reviews: {
    rating: number
    review_count: number
    reviews: string[]
  }
  seller_info: {
    shop_id: string | null
    shop_name: string | null
    shop_level: string | null
  }
  shipping_info: {
    shipping_fee: number | null
    shipping_method: string | null
    estimated_delivery: string | null
  }
}

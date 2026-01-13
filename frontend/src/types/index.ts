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
    product_analysis: ProductAnalysis
    recommendations: Recommendation[]
    product_data: ProductData
  }
  error?: string
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

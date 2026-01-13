import axios from 'axios'
import { AnalyzeRequest, AnalyzeResponse, AnalysisResult } from '../types'

// Vite 프록시를 사용하므로 상대 경로 사용
// 개발 환경: Vite 프록시가 /api 요청을 http://localhost:8000으로 전달
// 프로덕션: VITE_API_URL 환경 변수 사용
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const analyzeService = {
  /**
   * 분석 시작
   */
  async startAnalysis(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    const response = await api.post<AnalyzeResponse>('/api/v1/analyze', request)
    return response.data
  },

  /**
   * 분석 결과 조회
   */
  async getAnalysisResult(analysisId: string): Promise<AnalysisResult> {
    const response = await api.get<AnalysisResult>(`/api/v1/analyze/${analysisId}`)
    return response.data
  },

  /**
   * 분석 결과 폴링 (주기적으로 조회)
   */
  async pollAnalysisResult(
    analysisId: string,
    onUpdate: (result: AnalysisResult) => void,
    interval: number = 2000,
    maxAttempts: number = 30
  ): Promise<AnalysisResult> {
    let attempts = 0
    
    const poll = async (): Promise<AnalysisResult> => {
      attempts++
      const result = await this.getAnalysisResult(analysisId)
      
      onUpdate(result)
      
      if (result.status === 'completed' || result.status === 'failed') {
        return result
      }
      
      if (attempts >= maxAttempts) {
        throw new Error('Analysis timeout')
      }
      
      await new Promise(resolve => setTimeout(resolve, interval))
      return poll()
    }
    
    return poll()
  },

  /**
   * 리포트 다운로드
   */
  async downloadReport(analysisId: string, format: 'pdf' | 'excel' | 'markdown'): Promise<Blob> {
    const response = await api.get(
      `/api/v1/analyze/${analysisId}/download?format=${format}`,
      { responseType: 'blob' }
    )
    return response.data
  },
}

export const adminService = {
  /**
   * 점수 통계 조회
   */
  async getScoreStatistics(days: number = 30) {
    const response = await api.get(`/api/v1/admin/statistics/score?days=${days}`)
    return response.data
  },

  /**
   * 분석 통계 조회
   */
  async getAnalysisStatistics(days: number = 30) {
    const response = await api.get(`/api/v1/admin/statistics/analysis?days=${days}`)
    return response.data
  },

  /**
   * 분석 로그 조회
   */
  async getAnalysisLogs(params: { limit?: number; offset?: number; status?: string; start_date?: string; end_date?: string }) {
    const response = await api.get('/api/v1/admin/analysis-logs', { params })
    return response.data
  },

  /**
   * 에러 로그 조회
   */
  async getErrorLogs(params: { limit?: number; offset?: number; start_date?: string; end_date?: string }) {
    const response = await api.get('/api/v1/admin/error-logs', { params })
    return response.data
  },

  /**
   * 사용자 분석 로그 조회
   */
  async getUserAnalysisLogs(params: { url?: string; limit?: number; offset?: number }) {
    const response = await api.get('/api/v1/admin/user-logs', { params })
    return response.data
  },

  /**
   * 분석 결과 리스트 조회
   */
  async getAnalysisResultsList(params: { limit?: number; offset?: number; min_score?: number; max_score?: number; url_type?: string }) {
    const response = await api.get('/api/v1/admin/analysis-results', { params })
    return response.data
  },

  /**
   * AI 인사이트 리포트 조회
   */
  async getAIInsightReport(days: number = 30) {
    const response = await api.get(`/api/v1/admin/ai-insight-report?days=${days}`)
    return response.data
  },
}

export default api

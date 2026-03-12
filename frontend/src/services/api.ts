import axios from 'axios'
import { AnalyzeRequest, AnalyzeResponse, AnalysisResult } from '../types'

// Vite 프록시를 사용하므로 상대 경로 사용
// 개발 환경: Vite 프록시가 /api 요청을 http://localhost:8000으로 전달
// 프로덕션: VITE_API_URL 환경 변수 사용 (미설정 시 같은 오리진으로 요청 → Vercel에서 405 발생)
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

/** 배포 환경에서 API URL 미설정 시 사용자 안내용 */
function ensureApiBaseUrl(): void {
  if (API_BASE_URL) return
  const isProduction = typeof window !== 'undefined' &&
    window.location.hostname !== 'localhost' &&
    window.location.hostname !== '127.0.0.1'
  if (isProduction) {
    throw new Error(
      'API 서버 URL이 설정되지 않았습니다. Vercel 프로젝트 설정 → Environment Variables에서 VITE_API_URL에 백엔드 URL(예: https://xxx.railway.app)을 넣은 뒤 재배포해주세요.'
    )
  }
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000,  // 60초 타임아웃 (기본)
})

/** 백엔드 연결 확인 (짧은 타임아웃). 실패 시 분석 시작 전 안내용으로 사용 */
export async function checkApiHealth(): Promise<boolean> {
  try {
    await api.get('/health', { timeout: 3000 })
    return true
  } catch {
    return false
  }
}

export const analyzeService = {
  /**
   * 분석 시작 (백엔드가 즉시 analysis_id 반환, 분석은 백그라운드 진행)
   */
  async startAnalysis(request: AnalyzeRequest): Promise<AnalyzeResponse> {
    ensureApiBaseUrl()
    try {
      const response = await api.post<AnalyzeResponse>('/api/v1/analyze', request, {
        timeout: 60000,  // 분석 시작 요청: 60초 (프록시/콜드스타트 대비)
      })
      return response.data
    } catch (error: any) {
      if (error.code === 'ECONNABORTED') {
        throw new Error('요청 시간이 초과되었습니다. API 서버가 실행 중인지 확인하고 다시 시도해주세요.')
      }
      if (error.code === 'ECONNREFUSED' || error.message?.includes('Network Error')) {
        throw new Error('API 서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요.')
      }
      if (error.response) {
        const errorMessage = error.response.data?.detail ?? error.response.data?.message ?? '분석 시작에 실패했습니다.'
        throw new Error(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage))
      }
      throw error
    }
  },

  /**
   * 분석 결과 조회 (단일 요청 타임아웃 30초)
   */
  async getAnalysisResult(analysisId: string): Promise<AnalysisResult> {
    const response = await api.get<AnalysisResult>(`/api/v1/analyze/${analysisId}`, {
      timeout: 30000
    })
    return response.data
  },

  /**
   * 분석 결과 폴링 (임베딩·AI 분석 등으로 2~5분 소요될 수 있음)
   */
  async pollAnalysisResult(
    analysisId: string,
    onUpdate: (result: AnalysisResult) => void,
    interval: number = 2000,   // 2초 간격 (서버 부하 완화)
    maxAttempts: number = 180  // 최대 6분 대기 (180 × 2초)
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
        throw new Error('분석이 예상보다 오래 걸리고 있습니다. 이 페이지를 새로고침하면 완료된 결과를 볼 수 있습니다.')
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

export const errorReportingService = {
  /**
   * 오류 신고
   */
  async reportError(data: {
    analysis_id: string
    field_name: string
    issue_type: 'mismatch' | 'missing' | 'incorrect'
    severity: 'high' | 'medium' | 'low'
    user_description?: string
    crawler_value?: any
    report_value?: any
  }) {
    const response = await api.post('/api/v1/error/report', data)
    return response.data
  },

  /**
   * 오류 신고 목록 조회
   */
  async getErrorReports(fieldName?: string, status: string = 'pending', limit: number = 50) {
    const params = new URLSearchParams()
    if (fieldName) params.append('field_name', fieldName)
    params.append('status', status)
    params.append('limit', limit.toString())
    
    const response = await api.get(`/api/v1/error/reports?${params.toString()}`)
    return response.data
  },

  /**
   * 우선 크롤링 필드 목록 조회
   */
  async getPriorityFields() {
    const response = await api.get('/api/v1/error/priority-fields')
    return response.data
  },
}

// 편의 함수
export const reportError = errorReportingService.reportError

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

export const chatService = {
  /**
   * 챗봇 메시지 전송
   */
  async sendMessage(data: {
    message: string
    analysisId?: string
    analysisResult?: any
  }) {
    const response = await api.post('/api/v1/chat', {
      message: data.message,
      analysis_id: data.analysisId,
      analysis_result: data.analysisResult
    })
    return response.data
  },
}

export default api

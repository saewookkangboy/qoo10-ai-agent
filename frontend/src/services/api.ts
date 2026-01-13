import axios from 'axios'
import { AnalyzeRequest, AnalyzeResponse, AnalysisResult } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'

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
}

export default api

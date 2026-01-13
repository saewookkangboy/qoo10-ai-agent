import { useState } from 'react'
import { analyzeService } from '../services/api'

interface DownloadButtonProps {
  format: 'pdf' | 'excel' | 'markdown'
  label: string
  color: string
  analysisId: string
}

function DownloadButton({ format, label, color, analysisId }: DownloadButtonProps) {
  const [downloading, setDownloading] = useState(false)

  const handleDownload = async () => {
    if (!analysisId) return

    setDownloading(true)
    try {
      const blob = await analyzeService.downloadReport(analysisId, format)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `analysis_report_${analysisId}.${format === 'excel' ? 'xlsx' : format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      console.error('Download failed:', error)
      alert('다운로드에 실패했습니다.')
    } finally {
      setDownloading(false)
    }
  }

  return (
    <button
      onClick={handleDownload}
      disabled={downloading || !analysisId}
      className={`px-4 sm:px-6 py-2 sm:py-3 text-white rounded-lg font-medium transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed ${color}`}
    >
      {downloading ? '다운로드 중...' : label}
    </button>
  )
}

export default DownloadButton

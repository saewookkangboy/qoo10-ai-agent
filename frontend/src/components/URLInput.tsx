import { useState, useEffect } from 'react'

interface URLInputProps {
  url: string
  onChange: (url: string) => void
  onSubmit: (e: React.FormEvent) => void
  loading: boolean
  error: string | null
}

function URLInput({ url, onChange, onSubmit, loading, error }: URLInputProps) {
  const [isValid, setIsValid] = useState(true)

  useEffect(() => {
    if (url) {
      const qoo10Pattern = /qoo10\.(jp|com)/
      setIsValid(qoo10Pattern.test(url))
    } else {
      setIsValid(true)
    }
  }, [url])

  return (
    <form onSubmit={onSubmit} className="space-y-4 sm:space-y-5">
      <div>
        <label htmlFor="url" className="block text-sm sm:text-base font-medium text-[#1A1A1A] mb-2 sm:mb-3">
          상품 또는 Shop URL
        </label>
        <input
          type="url"
          id="url"
          value={url}
          onChange={(e) => onChange(e.target.value)}
          placeholder="https://www.qoo10.jp/gmkt.inc/Goods/Goods.aspx?goodscode=..."
          className={`w-full px-4 sm:px-5 py-3 sm:py-4 text-sm sm:text-base border-2 rounded-lg focus:outline-none focus:ring-2 transition-all ${
            !isValid
              ? 'border-[#CC0000] focus:ring-[#CC0000] focus:border-[#CC0000]'
              : 'border-[#E6E6E6] focus:ring-[#0066CC] focus:border-[#0066CC]'
          } disabled:bg-[#F5F5F5] disabled:cursor-not-allowed text-[#1A1A1A] placeholder-[#808080]`}
          disabled={loading}
        />
        {!isValid && (
          <p className="mt-2 text-xs sm:text-sm text-[#CC0000] flex items-center gap-1">
            <span>⚠️</span>
            <span>올바른 Qoo10 URL을 입력하세요</span>
          </p>
        )}
        {error && (
          <p className="mt-2 text-xs sm:text-sm text-[#CC0000] flex items-center gap-1">
            <span>⚠️</span>
            <span>{error}</span>
          </p>
        )}
      </div>
      <button
        type="submit"
        disabled={!url || !isValid || loading}
        className="w-full bg-[#0066CC] text-white py-3 sm:py-4 px-6 sm:px-8 rounded-lg font-semibold text-base sm:text-lg hover:bg-[#004499] disabled:bg-[#808080] disabled:cursor-not-allowed transition-all duration-200 shadow-[0_2px_4px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_8px_rgba(0,0,0,0.12)] active:scale-[0.98]"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>분석 중...</span>
          </span>
        ) : (
          '분석 시작'
        )}
      </button>
    </form>
  )
}

export default URLInput

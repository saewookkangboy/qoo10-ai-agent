import { useState, useEffect, useRef } from 'react'

interface HelpTooltipProps {
  content: string
  position?: 'top' | 'bottom' | 'left' | 'right'
}

function HelpTooltip({ content, position = 'top' }: HelpTooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const tooltipRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  // 외부 클릭 시 툴팁 닫기
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        tooltipRef.current &&
        buttonRef.current &&
        !tooltipRef.current.contains(event.target as Node) &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setIsVisible(false)
      }
    }

    if (isVisible) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isVisible])

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2'
  }

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-gray-800 border-l-transparent border-r-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-gray-800 border-l-transparent border-r-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-gray-800 border-t-transparent border-b-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-gray-800 border-t-transparent border-b-transparent border-l-transparent'
  }

  return (
    <div className="relative inline-block">
      <button
        ref={buttonRef}
        type="button"
        className="inline-flex items-center justify-center w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-gray-200 hover:bg-gray-300 active:bg-gray-400 text-gray-600 hover:text-gray-800 text-xs sm:text-sm font-medium transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onClick={(e) => {
          e.stopPropagation()
          setIsVisible(!isVisible)
        }}
        aria-label="도움말"
        aria-expanded={isVisible}
      >
        ?
      </button>
      
      {isVisible && (
        <div
          ref={tooltipRef}
          className={`absolute z-50 ${positionClasses[position]} w-64 sm:w-72 p-3 sm:p-4 bg-gray-800 text-white text-xs sm:text-sm rounded-lg shadow-xl`}
          onMouseEnter={() => setIsVisible(true)}
          onMouseLeave={() => setIsVisible(false)}
          role="tooltip"
        >
          <div className={`absolute ${arrowClasses[position]} border-4`}></div>
          <p className="leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>
      )}
    </div>
  )
}

export default HelpTooltip

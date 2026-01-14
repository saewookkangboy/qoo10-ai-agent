import { useEffect, useRef } from 'react'
import { VChart } from '@visactor/vchart'
import { useTheme } from '../../contexts/ThemeContext'

interface ScoreGaugeChartProps {
  score: number
  title: string
  color?: string
  size?: number
}

export default function ScoreGaugeChart({ 
  score, 
  title, 
  color = '#0066CC',
  size = 200 
}: ScoreGaugeChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstanceRef = useRef<VChart | null>(null)
  const { actualTheme } = useTheme()

  useEffect(() => {
    if (!chartRef.current) return

    const isDark = actualTheme === 'dark'
    const textColor = isDark ? '#F3F4F6' : '#1F2937'
    const bgColor = isDark ? '#111827' : '#FFFFFF'

    const spec = {
      type: 'gauge',
      data: [
        {
          id: 'gauge',
          values: [{ value: score, type: 'score' }]
        }
      ],
      categoryField: 'type',
      valueField: 'value',
      innerRadius: 0.7,
      startAngle: -180,
      endAngle: 0,
      gauge: {
        type: 'circularProgress',
        progress: {
          style: {
            fill: color,
            cornerRadius: 4
          }
        },
        track: {
          style: {
            fill: isDark ? '#374151' : '#E5E7EB',
            cornerRadius: 4
          }
        },
        tickMask: {
          visible: false
        },
        label: {
          visible: true,
          style: {
            fill: textColor,
            fontSize: 24,
            fontWeight: 'bold'
          },
          formatMethod: (datum: any) => `${datum.value}`
        }
      },
      pointer: {
        visible: false
      },
      background: 'transparent'
    }

    const chartInstance = new VChart(spec, {
      dom: chartRef.current,
      width: size,
      height: size / 2,
      theme: isDark ? 'dark' : 'light'
    })

    chartInstance.renderSync()
    chartInstanceRef.current = chartInstance

    return () => {
      chartInstance.release()
    }
  }, [score, title, color, size, actualTheme])

  return (
    <div className="flex flex-col items-center">
      <div ref={chartRef} className="w-full" style={{ height: `${size / 2}px` }} />
      <p className="mt-2 text-sm font-medium text-gray-700 dark:text-gray-300">{title}</p>
    </div>
  )
}

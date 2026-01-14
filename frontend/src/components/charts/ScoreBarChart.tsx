import { useEffect, useRef } from 'react'
import { VChart } from '@visactor/vchart'
import { useTheme } from '../../contexts/ThemeContext'

interface ScoreData {
  category: string
  score: number
  color?: string
}

interface ScoreBarChartProps {
  data: ScoreData[]
  height?: number
}

export default function ScoreBarChart({ data, height = 300 }: ScoreBarChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstanceRef = useRef<VChart | null>(null)
  const { actualTheme } = useTheme()

  useEffect(() => {
    if (!chartRef.current || data.length === 0) return

    const isDark = actualTheme === 'dark'
    const textColor = isDark ? '#F3F4F6' : '#1F2937'
    const gridColor = isDark ? '#374151' : '#E5E7EB'

    const spec = {
      type: 'bar',
      background: 'transparent',
      width: chartRef.current.offsetWidth,
      height: height,
      data: [
        {
          id: 'scores',
          values: data.map(item => ({
            category: item.category,
            score: item.score,
            color: item.color || '#0066CC'
          }))
        }
      ],
      xField: 'category',
      yField: 'score',
      bar: {
        style: {
          fill: (datum: any) => datum.color,
          cornerRadius: 4
        }
      },
      axes: [
        {
          orient: 'left',
          domainLine: { visible: false },
          tick: {
            visible: true,
            style: {
              fill: textColor,
              fontSize: 12
            }
          },
          grid: {
            visible: true,
            style: {
              stroke: gridColor,
              lineDash: [4, 4]
            }
          },
          label: {
            visible: true,
            style: {
              fill: textColor,
              fontSize: 12
            }
          }
        },
        {
          orient: 'bottom',
          domainLine: { visible: false },
          tick: {
            visible: true,
            style: {
              fill: textColor,
              fontSize: 12
            }
          },
          label: {
            visible: true,
            style: {
              fill: textColor,
              fontSize: 12
            }
          }
        }
      ],
      label: {
        visible: true,
        position: 'top',
        offset: 5,
        style: {
          fill: textColor,
          fontSize: 14,
          fontWeight: 'bold',
          fontFamily: 'system-ui, -apple-system, sans-serif'
        },
        formatMethod: (datum: any) => `${datum.score}점`
      }
    }

    const chartInstance = new VChart(spec, {
      dom: chartRef.current,
      theme: isDark ? 'dark' : 'light'
    })

    chartInstance.renderSync()
    chartInstanceRef.current = chartInstance

    const handleResize = () => {
      if (chartRef.current && chartInstanceRef.current) {
        chartInstanceRef.current.updateSpec({
          width: chartRef.current.offsetWidth
        })
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chartInstance.release()
    }
  }, [data, height, actualTheme])

  return <div ref={chartRef} className="w-full" style={{ height: `${height}px` }} />
}

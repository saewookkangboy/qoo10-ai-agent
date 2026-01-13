interface StatCardProps {
  title: string
  value: number | string
  subtitle?: string
  icon: string
  color: 'blue' | 'green' | 'purple' | 'red' | 'yellow'
}

function StatCard({ title, value, subtitle, icon, color }: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-700',
    green: 'bg-green-50 border-green-200 text-green-700',
    purple: 'bg-purple-50 border-purple-200 text-purple-700',
    red: 'bg-red-50 border-red-200 text-red-700',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-700',
  }

  return (
    <div className="bg-white rounded-lg shadow-[0_2px_4px_rgba(0,0,0,0.08)] p-4 sm:p-6">
      <div className="flex items-center justify-between mb-3 sm:mb-4">
        <h3 className="text-sm sm:text-base font-medium text-[#4D4D4D]">{title}</h3>
        <span className="text-xl sm:text-2xl">{icon}</span>
      </div>
      <div className={`px-3 sm:px-4 py-2 sm:py-3 rounded-lg border ${colorClasses[color]}`}>
        <div className="text-2xl sm:text-3xl font-bold mb-1">{value}</div>
        {subtitle && (
          <div className="text-xs sm:text-sm opacity-75">{subtitle}</div>
        )}
      </div>
    </div>
  )
}

export default StatCard

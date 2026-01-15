function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center">
      <div className="relative">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-200/50 dark:border-blue-800/50"></div>
        <div className="animate-spin rounded-full h-12 w-12 border-t-4 border-blue-600 dark:border-blue-400 absolute top-0 left-0"></div>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 dark:from-blue-400 dark:to-purple-500 opacity-75"></div>
        </div>
      </div>
    </div>
  )
}

export default LoadingSpinner

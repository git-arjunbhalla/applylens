function LoadingState({ message = 'Loading…' }) {
  return (
    <div className="flex items-center gap-3 text-muted" role="status">
      <span className="h-2 w-8 animate-pulse rounded-full bg-accent" aria-hidden="true" />
      <p>{message}</p>
    </div>
  )
}

export default LoadingState

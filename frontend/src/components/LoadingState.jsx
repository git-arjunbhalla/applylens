function LoadingState({ message = 'Loading…' }) {
  return (
    <p className="text-neutral-600" role="status">
      {message}
    </p>
  )
}

export default LoadingState

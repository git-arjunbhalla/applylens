function ErrorState({ message, onRetry }) {
  return (
    <div className="rounded border border-red-200 bg-red-50 px-3 py-3 text-sm text-red-800" role="alert">
      <p>{message}</p>
      {onRetry ? (
        <button
          className="mt-2 rounded border border-red-300 px-2 py-1 text-red-900"
          type="button"
          onClick={onRetry}
        >
          Try again
        </button>
      ) : null}
    </div>
  )
}

export default ErrorState

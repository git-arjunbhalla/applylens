import Button from './Button'

function ErrorState({ message, onRetry }) {
  return (
    <div className="rounded-md border border-danger-line bg-danger-bg px-3 py-3 text-sm text-danger" role="alert">
      <p>{message}</p>
      {onRetry ? (
        <Button className="mt-2" variant="secondary" type="button" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  )
}

export default ErrorState

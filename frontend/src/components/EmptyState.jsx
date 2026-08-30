function EmptyState({ title, message, action }) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-surface px-4 py-10 text-center">
      <h2 className="font-display text-lg font-medium text-ink">{title}</h2>
      {message ? <p className="mt-2 text-muted">{message}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}

export default EmptyState

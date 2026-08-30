function EmptyState({ title, message, action }) {
  return (
    <div className="rounded border border-neutral-200 px-4 py-8 text-center">
      <h2 className="text-lg font-medium text-neutral-900">{title}</h2>
      {message ? <p className="mt-2 text-neutral-600">{message}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}

export default EmptyState

function StatusBadge({ status }) {
  return (
    <span className="inline-flex rounded border border-neutral-300 px-2 py-0.5 text-sm text-neutral-800">
      {status}
    </span>
  )
}

export default StatusBadge

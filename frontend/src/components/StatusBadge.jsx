const statusStyles = {
  Wishlist: 'border-line bg-canvas text-ink',
  Applied: 'border-amber-300/70 bg-amber-100 text-amber-950 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100',
  OA: 'border-orange-300/80 bg-orange-100 text-orange-950 dark:border-orange-800 dark:bg-orange-950 dark:text-orange-100',
  Interviewing: 'border-accent/40 bg-accent-soft text-ink',
  Offer: 'border-emerald-300 bg-emerald-50 text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-100',
  Rejected: 'border-line bg-canvas text-muted',
}

function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-0.5 text-sm ${statusStyles[status] ?? 'border-line bg-canvas text-ink'}`}
    >
      {status}
    </span>
  )
}

export default StatusBadge

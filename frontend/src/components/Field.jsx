export const inputClass =
  'w-full rounded-md border border-line bg-surface px-3 py-2 text-ink placeholder:text-muted/80 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent'

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="text-sm text-muted">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  )
}

export default Field

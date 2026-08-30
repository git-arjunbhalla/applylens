const widths = {
  default: 'max-w-5xl',
  narrow: 'max-w-2xl',
  form: 'max-w-md',
}

function Page({ children, width = 'default', className = '' }) {
  return (
    <main className={`page-enter mx-auto ${widths[width]} px-4 py-8 sm:px-6 sm:py-10 ${className}`}>
      {children}
    </main>
  )
}

export function PageHeader({ title, description, action }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="font-display text-3xl font-semibold tracking-tight text-ink">{title}</h1>
        {description ? <p className="mt-2 text-muted">{description}</p> : null}
      </div>
      {action}
    </div>
  )
}

export default Page

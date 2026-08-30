import BrandMark from './BrandMark'
import ThemeToggle from './ThemeToggle'

function GuestLayout({ children }) {
  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="flex items-center justify-between px-4 py-4 sm:px-6">
        <div className="flex items-center gap-2 text-ink">
          <BrandMark className="h-8 w-8" />
          <span className="font-display text-lg font-semibold tracking-tight">ApplyLens</span>
        </div>
        <ThemeToggle />
      </header>
      <div className="mx-auto max-w-md px-4 py-8 sm:px-6 sm:py-12">{children}</div>
    </div>
  )
}

export default GuestLayout

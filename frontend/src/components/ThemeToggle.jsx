import { useTheme } from '../hooks/useTheme'
import { buttonClass } from './Button'

function ThemeToggle() {
  const { resolvedTheme, toggleTheme } = useTheme()
  const isDark = resolvedTheme === 'dark'

  return (
    <button
      className={buttonClass('secondary', 'min-h-10 min-w-10 px-2.5')}
      type="button"
      onClick={toggleTheme}
      aria-pressed={isDark}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
    >
      <span aria-hidden="true">{isDark ? 'Light' : 'Dark'}</span>
    </button>
  )
}

export default ThemeToggle

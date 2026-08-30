const variants = {
  primary:
    'bg-linear-to-r from-amber-300 to-accent text-accent-ink shadow-sm hover:brightness-105',
  secondary: 'border border-line bg-surface text-ink hover:bg-accent-soft/40',
  danger: 'bg-danger text-white dark:text-accent-ink hover:brightness-110',
  ghost: 'text-ink underline-offset-4 hover:underline',
}

export function buttonClass(variant = 'primary', extra = '') {
  return [
    'inline-flex items-center justify-center rounded-md px-3 py-2 text-sm font-medium',
    'transition-[filter,background-color,color] duration-150',
    'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent',
    'disabled:pointer-events-none disabled:opacity-60',
    variants[variant] ?? variants.primary,
    extra,
  ]
    .filter(Boolean)
    .join(' ')
}

function Button({ variant = 'primary', className = '', type = 'button', ...props }) {
  return <button className={buttonClass(variant, className)} type={type} {...props} />
}

export default Button

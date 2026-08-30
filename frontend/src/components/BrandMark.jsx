function BrandMark({ className = 'h-8 w-8', title = 'ApplyLens' }) {
  return (
    <svg
      className={className}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label={title}
    >
      <title>{title}</title>
      <circle cx="15" cy="15" r="10.25" stroke="currentColor" strokeWidth="2.2" />
      <circle cx="15" cy="15" r="4.1" stroke="var(--al-accent)" strokeWidth="2" />
      <path
        d="M18.2 22.4h6.3c.6 0 1.1.5 1.1 1.1v4.4c0 .6-.5 1.1-1.1 1.1h-7.4c-.6 0-1.1-.5-1.1-1.1v-3.3"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <path d="M18.2 22.4 21.4 19.6H24.5v2.8" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
      <path
        d="M13.1 15.2 14.5 16.7 17.2 13.6"
        stroke="var(--al-accent)"
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

export default BrandMark

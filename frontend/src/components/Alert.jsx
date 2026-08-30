function Alert({ children, className = '' }) {
  return (
    <p
      className={`rounded-md border border-danger-line bg-danger-bg px-3 py-2 text-sm text-danger ${className}`}
      role="alert"
    >
      {children}
    </p>
  )
}

export default Alert

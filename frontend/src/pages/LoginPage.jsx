import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { getApiErrorMessage, validateEmail, validatePassword } from '../services/authErrors'

function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const fromPath = location.state?.from?.pathname
  const redirectTo =
    fromPath && fromPath !== '/login' && fromPath !== '/signup' ? fromPath : '/'

  async function handleSubmit(event) {
    event.preventDefault()
    const emailError = validateEmail(email)
    const passwordError = validatePassword(password)
    if (emailError || passwordError) {
      setError(emailError || passwordError)
      return
    }

    setError('')
    setIsSubmitting(true)
    try {
      await login({ email: email.trim(), password })
      navigate(redirectTo, { replace: true })
    } catch (err) {
      setError(getApiErrorMessage(err, 'Invalid email or password'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="mx-auto max-w-md px-6 py-16">
      <h1 className="text-2xl font-semibold text-neutral-900">Log in</h1>
      <p className="mt-2 text-neutral-600">Sign in to continue to ApplyLens.</p>

      <form className="mt-8 space-y-4" onSubmit={handleSubmit} noValidate>
        {error ? (
          <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800" role="alert">
            {error}
          </p>
        ) : null}

        <label className="block">
          <span className="text-sm text-neutral-700">Email</span>
          <input
            className="mt-1 w-full rounded border border-neutral-300 px-3 py-2"
            type="email"
            name="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>

        <label className="block">
          <span className="text-sm text-neutral-700">Password</span>
          <input
            className="mt-1 w-full rounded border border-neutral-300 px-3 py-2"
            type="password"
            name="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>

        <button
          className="w-full rounded bg-neutral-900 px-3 py-2 text-white disabled:opacity-60"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Logging in…' : 'Log in'}
        </button>
      </form>

      <p className="mt-6 text-sm text-neutral-600">
        Need an account?{' '}
        <Link className="underline" to="/signup">
          Sign up
        </Link>
      </p>
    </main>
  )
}

export default LoginPage

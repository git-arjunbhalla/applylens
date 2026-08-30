import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import Alert from '../components/Alert'
import Button from '../components/Button'
import Field, { inputClass } from '../components/Field'
import GuestLayout from '../components/GuestLayout'
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
    <GuestLayout>
      <main>
        <h1 className="font-display text-3xl font-semibold tracking-tight text-ink">Log in</h1>
        <p className="mt-2 text-muted">Sign in to continue to ApplyLens.</p>

        <form className="mt-8 space-y-4" onSubmit={handleSubmit} noValidate>
          {error ? <Alert>{error}</Alert> : null}

          <Field label="Email">
            <input
              className={inputClass}
              type="email"
              name="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </Field>

          <Field label="Password">
            <input
              className={inputClass}
              type="password"
              name="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </Field>

          <Button className="w-full" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Logging in…' : 'Log in'}
          </Button>
        </form>

        <p className="mt-6 text-sm text-muted">
          Need an account?{' '}
          <Link className="font-medium text-ink underline underline-offset-4" to="/signup">
            Sign up
          </Link>
        </p>
      </main>
    </GuestLayout>
  )
}

export default LoginPage

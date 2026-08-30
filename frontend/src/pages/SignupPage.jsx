import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Alert from '../components/Alert'
import Button from '../components/Button'
import Field, { inputClass } from '../components/Field'
import GuestLayout from '../components/GuestLayout'
import { useAuth } from '../hooks/useAuth'
import { getApiErrorMessage, validateEmail, validatePassword } from '../services/authErrors'

function SignupPage() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    const emailError = validateEmail(email)
    const passwordError = validatePassword(password, { minLength: 8 })
    if (emailError || passwordError) {
      setError(emailError || passwordError)
      return
    }

    setError('')
    setIsSubmitting(true)
    try {
      await signup({ email: email.trim(), password })
      navigate('/', { replace: true })
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to create your account.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <GuestLayout>
      <main>
        <h1 className="font-display text-3xl font-semibold tracking-tight text-ink">Sign up</h1>
        <p className="mt-2 text-muted">Create an ApplyLens account.</p>

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
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          </Field>

          <Button className="w-full" type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating account…' : 'Create account'}
          </Button>
        </form>

        <p className="mt-6 text-sm text-muted">
          Already have an account?{' '}
          <Link className="font-medium text-ink underline underline-offset-4" to="/login">
            Log in
          </Link>
        </p>
      </main>
    </GuestLayout>
  )
}

export default SignupPage

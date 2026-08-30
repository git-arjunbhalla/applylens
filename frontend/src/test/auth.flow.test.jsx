import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import App from '../App'
import { getAccessToken, getStoredRefreshToken } from '../services/api'
import { installApiMock, sampleUser, tokenPayload } from './mockApi'

function renderApp(initialPath = '/') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <App />
    </MemoryRouter>,
  )
}

describe('frontend authentication flows', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('blocks unauthenticated users from protected content', async () => {
    installApiMock({})
    renderApp('/')

    expect(await screen.findByRole('heading', { name: /log in/i })).toBeInTheDocument()
    expect(screen.queryByText(/you are signed in/i)).not.toBeInTheDocument()
  })

  it('signs up, stores tokens, and shows the authenticated page', async () => {
    const user = userEvent.setup()
    installApiMock({
      'post /api/v1/auth/signup': () => ({
        status: 201,
        data: tokenPayload(),
      }),
    })

    renderApp('/signup')

    await user.type(await screen.findByLabelText(/email/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByText(/you are signed in as user@example.com/i)).toBeInTheDocument()
    expect(getAccessToken()).toBe('access-token')
    expect(getStoredRefreshToken()).toBe('refresh-token')
  })

  it('shows a duplicate signup error', async () => {
    const user = userEvent.setup()
    installApiMock({
      'post /api/v1/auth/signup': () => ({
        status: 409,
        data: { detail: 'An account with this email already exists' },
      }),
    })

    renderApp('/signup')

    await user.type(await screen.findByLabelText(/email/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'An account with this email already exists',
    )
    expect(screen.getByRole('heading', { name: /sign up/i })).toBeInTheDocument()
  })

  it('logs in and reaches protected content', async () => {
    const user = userEvent.setup()
    installApiMock({
      'post /api/v1/auth/login': () => ({
        status: 200,
        data: tokenPayload(),
      }),
    })

    renderApp('/login')

    await user.type(await screen.findByLabelText(/email/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /log in/i }))

    expect(await screen.findByText(/you are signed in as user@example.com/i)).toBeInTheDocument()
  })

  it('handles invalid credentials without exposing internals', async () => {
    const user = userEvent.setup()
    installApiMock({
      'post /api/v1/auth/login': () => ({
        status: 401,
        data: { detail: 'Invalid email or password' },
      }),
    })

    renderApp('/login')

    await user.type(await screen.findByLabelText(/email/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'wrong-password')
    await user.click(screen.getByRole('button', { name: /log in/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password')
    expect(screen.queryByText(/stack/i)).not.toBeInTheDocument()
    expect(getAccessToken()).toBeNull()
  })

  it('logs out and clears stored credentials', async () => {
    const user = userEvent.setup()
    installApiMock({
      'post /api/v1/auth/login': () => ({
        status: 200,
        data: tokenPayload(),
      }),
    })

    renderApp('/login')

    await user.type(await screen.findByLabelText(/email/i), 'user@example.com')
    await user.type(screen.getByLabelText(/password/i), 'password123')
    await user.click(screen.getByRole('button', { name: /log in/i }))
    await screen.findByRole('button', { name: /log out/i })

    await user.click(screen.getByRole('button', { name: /log out/i }))

    expect(await screen.findByRole('heading', { name: /log in/i })).toBeInTheDocument()
    expect(getAccessToken()).toBeNull()
    expect(getStoredRefreshToken()).toBeNull()
  })

  it('restores a session from the stored refresh token via /me', async () => {
    window.localStorage.setItem('applylens.refresh_token', 'refresh-token')
    const { requests } = installApiMock({
      'post /api/v1/auth/refresh': () => ({
        status: 200,
        data: tokenPayload({ access_token: 'restored-access' }),
      }),
      'get /api/v1/auth/me': () => ({ status: 200, data: sampleUser }),
    })

    renderApp('/')

    expect(await screen.findByText(/you are signed in as user@example.com/i)).toBeInTheDocument()
    expect(getAccessToken()).toBe('restored-access')
    expect(requests.some((request) => request.path === '/api/v1/auth/me')).toBe(true)
    expect(requests.find((request) => request.path === '/api/v1/auth/me').authorization).toBe(
      'Bearer restored-access',
    )
  })

  it('returns to login when session restore refresh fails', async () => {
    window.localStorage.setItem('applylens.refresh_token', 'expired-refresh')
    installApiMock({
      'post /api/v1/auth/refresh': () => ({
        status: 401,
        data: { detail: 'Token has expired' },
      }),
    })

    renderApp('/')

    expect(await screen.findByRole('heading', { name: /log in/i })).toBeInTheDocument()
    await waitFor(() => {
      expect(getStoredRefreshToken()).toBeNull()
    })
  })

  it('validates signup fields before calling the API', async () => {
    const user = userEvent.setup()
    const { requests } = installApiMock({
      'post /api/v1/auth/signup': () => ({
        status: 201,
        data: tokenPayload(),
      }),
    })

    renderApp('/signup')

    await user.type(await screen.findByLabelText(/email/i), 'not-an-email')
    await user.type(screen.getByLabelText(/password/i), 'short')
    await user.click(screen.getByRole('button', { name: /create account/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Enter a valid email address.')
    expect(requests).toHaveLength(0)
  })
})

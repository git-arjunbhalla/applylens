import { beforeEach, describe, expect, it } from 'vitest'
import api, {
  applyAuthSession,
  getAccessToken,
  getStoredRefreshToken,
  resetAuthClientState,
} from './api'
import { authorizationHeader, installApiMock, parseRequestData, sampleUser, tokenPayload } from '../test/mockApi'

describe('API client authentication', () => {
  beforeEach(() => {
    resetAuthClientState()
  })

  it('attaches the access token to authenticated requests', async () => {
    applyAuthSession(tokenPayload())
    const { requests } = installApiMock({
      'get /api/v1/auth/me': () => ({ status: 200, data: sampleUser }),
    })

    await api.get('/api/v1/auth/me')

    expect(requests).toHaveLength(1)
    expect(requests[0].authorization).toBe('Bearer access-token')
  })

  it('refreshes an expired access token and retries the original request', async () => {
    applyAuthSession(
      tokenPayload({ access_token: 'expired-access', refresh_token: 'refresh-token' }),
    )

    const { requests } = installApiMock({
      'get /api/v1/auth/me': (config) => {
        if (authorizationHeader(config) === 'Bearer expired-access') {
          return { status: 401, data: { detail: 'Token has expired' } }
        }
        return { status: 200, data: sampleUser }
      },
      'post /api/v1/auth/refresh': (config) => {
        expect(parseRequestData(config)).toEqual({
          refresh_token: 'refresh-token',
        })
        return {
          status: 200,
          data: tokenPayload({
            access_token: 'new-access',
            refresh_token: 'new-refresh',
          }),
        }
      },
    })

    const response = await api.get('/api/v1/auth/me')

    expect(response.data).toEqual(sampleUser)
    expect(getAccessToken()).toBe('new-access')
    expect(getStoredRefreshToken()).toBe('new-refresh')
    expect(requests.filter((request) => request.path === '/api/v1/auth/me')).toHaveLength(2)
    expect(requests.filter((request) => request.path === '/api/v1/auth/refresh')).toHaveLength(1)
    expect(requests[requests.length - 1].authorization).toBe('Bearer new-access')
  })

  it('does not loop when refresh fails after a 401', async () => {
    applyAuthSession(
      tokenPayload({ access_token: 'expired-access', refresh_token: 'bad-refresh' }),
    )

    const { requests } = installApiMock({
      'get /api/v1/auth/me': () => ({
        status: 401,
        data: { detail: 'Token has expired' },
      }),
      'post /api/v1/auth/refresh': () => ({
        status: 401,
        data: { detail: 'Invalid token' },
      }),
    })

    await expect(api.get('/api/v1/auth/me')).rejects.toThrow()

    expect(requests.filter((request) => request.path === '/api/v1/auth/me')).toHaveLength(1)
    expect(requests.filter((request) => request.path === '/api/v1/auth/refresh')).toHaveLength(1)
    expect(getAccessToken()).toBeNull()
    expect(getStoredRefreshToken()).toBeNull()
  })

  it('does not attempt refresh for failed login requests', async () => {
    const { requests } = installApiMock({
      'post /api/v1/auth/login': () => ({
        status: 401,
        data: { detail: 'Invalid email or password' },
      }),
      'post /api/v1/auth/refresh': () => ({
        status: 200,
        data: tokenPayload(),
      }),
    })

    await expect(
      api.post(
        '/api/v1/auth/login',
        { email: 'user@example.com', password: 'wrong' },
        { skipAuth: true, skipRefresh: true },
      ),
    ).rejects.toMatchObject({ response: { status: 401 } })

    expect(requests.some((request) => request.path === '/api/v1/auth/refresh')).toBe(false)
  })
})

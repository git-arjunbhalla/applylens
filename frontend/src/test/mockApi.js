import { AxiosError } from 'axios'
import api from '../services/api'

function requestPath(config) {
  const base = config.baseURL || 'http://api.test'
  const url = config.url || ''
  return new URL(url, base.endsWith('/') ? base : `${base}/`).pathname
}

export function parseRequestData(config) {
  if (typeof config.data === 'string') {
    try {
      return JSON.parse(config.data)
    } catch {
      return config.data
    }
  }
  return config.data
}

export function authorizationHeader(config) {
  const header = config.headers?.Authorization ?? config.headers?.authorization
  if (typeof header === 'string') {
    return header
  }
  if (header && typeof header.toString === 'function') {
    return header.toString()
  }
  return undefined
}

export function installApiMock(handlers) {
  const requests = []

  api.defaults.adapter = async (config) => {
    const method = (config.method || 'get').toLowerCase()
    const path = requestPath(config)
    const key = `${method} ${path}`
    requests.push({
      method,
      path,
      authorization: authorizationHeader(config),
      data: parseRequestData(config),
    })

    const handler = handlers[key]
    if (!handler) {
      const error = new AxiosError(`No mock for ${key}`)
      error.config = config
      error.response = {
        status: 404,
        data: { detail: `No mock for ${key}` },
        headers: {},
        config,
      }
      throw error
    }

    const result = await handler(config)
    const status = result.status ?? 200
    const data = result.data ?? {}

    if (status >= 400) {
      const error = new AxiosError(
        typeof data.detail === 'string' ? data.detail : `Request failed with status ${status}`,
      )
      error.config = config
      error.response = { status, data, headers: {}, config }
      throw error
    }

    return {
      data,
      status,
      statusText: 'OK',
      headers: {},
      config,
    }
  }

  return { requests }
}

export const sampleUser = {
  id: 1,
  email: 'user@example.com',
  created_at: '2026-01-01T00:00:00Z',
}

export function tokenPayload(overrides = {}) {
  return {
    access_token: 'access-token',
    refresh_token: 'refresh-token',
    token_type: 'bearer',
    user: sampleUser,
    ...overrides,
  }
}

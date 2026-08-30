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
      params: config.params ?? {},
      authorization: authorizationHeader(config),
      data: parseRequestData(config),
    })

    const handler = handlers[key] ?? defaultHandlers[key]
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
    const data = Object.prototype.hasOwnProperty.call(result, 'data') ? result.data : {}

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

export const emptyAnalyticsSummary = {
  total_applications: 0,
  counts_by_status: {
    Wishlist: 0,
    Applied: 0,
    OA: 0,
    Interviewing: 0,
    Offer: 0,
    Rejected: 0,
  },
  upcoming_deadlines: 0,
  interview_count: 0,
  offers: 0,
  rejections: 0,
  response_rate: 0,
  average_time_to_response_days: null,
}

const defaultHandlers = {
  'get /api/v1/analytics/summary': () => ({
    status: 200,
    data: emptyAnalyticsSummary,
  }),
  'get /api/v1/applications': () => ({
    status: 200,
    data: { items: [], total: 0, page: 1, page_size: 20 },
  }),
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

export function sampleApplication(overrides = {}) {
  return {
    id: 1,
    user_id: 1,
    company_name: 'Acme',
    role_title: 'Engineer',
    status: 'Applied',
    applied_date: '2026-01-15',
    deadline: '2026-02-01',
    notes: 'Follow up',
    job_description: 'Build things',
    resume_version: 'v1',
    created_at: '2026-01-10T00:00:00Z',
    updated_at: '2026-01-12T00:00:00Z',
    ...overrides,
  }
}

export function sampleInterview(overrides = {}) {
  return {
    id: 10,
    application_id: 1,
    round_name: 'Phone screen',
    scheduled_at: '2026-03-01T15:00:00Z',
    notes: 'Prep algorithms',
    outcome: 'Pending',
    ...overrides,
  }
}

export function sampleApplicationList(items, overrides = {}) {
  return {
    items,
    total: items.length,
    page: 1,
    page_size: 20,
    ...overrides,
  }
}

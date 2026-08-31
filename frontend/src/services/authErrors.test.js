import { describe, expect, it } from 'vitest'
import { getApiErrorMessage, validateEmail, validatePassword } from './authErrors'

describe('auth error helpers', () => {
  it('maps network failures to a user-facing message', () => {
    expect(getApiErrorMessage({})).toBe('Unable to reach the server. Please try again.')
  })

  it('uses FastAPI string details', () => {
    expect(
      getApiErrorMessage({
        response: { data: { detail: 'An account with this email already exists' } },
      }),
    ).toBe('An account with this email already exists')
  })

  it('joins FastAPI validation details', () => {
    expect(
      getApiErrorMessage({
        response: {
          data: {
            detail: [{ msg: 'String should have at least 8 characters' }],
          },
        },
      }),
    ).toBe('String should have at least 8 characters')
  })

  it('falls back for unexpected payloads', () => {
    expect(
      getApiErrorMessage({
        response: { data: { unexpected: true } },
      }),
    ).toBe('Something went wrong. Please try again.')
  })

  it('validates email and password', () => {
    expect(validateEmail('')).toBe('Email is required.')
    expect(validateEmail('bad')).toBe('Enter a valid email address.')
    expect(validateEmail('user@example.com')).toBeNull()
    expect(validatePassword('')).toBe('Password is required.')
    expect(validatePassword('short', { minLength: 8 })).toBe(
      'Password must be at least 8 characters.',
    )
    expect(validatePassword('a'.repeat(73))).toBe('Password must be at most 72 characters.')
  })

  it('surfaces 429 details without treating them as auth failures', () => {
    expect(
      getApiErrorMessage({
        response: {
          status: 429,
          data: { detail: 'AI request limit exceeded. Please try again later.' },
        },
      }),
    ).toBe('AI request limit exceeded. Please try again later.')
  })
})

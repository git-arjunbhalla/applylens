export function getApiErrorMessage(error, fallback = 'Something went wrong. Please try again.') {
  if (!error.response) {
    return 'Unable to reach the server. Please try again.'
  }

  const detail = error.response.data?.detail
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const messages = detail
      .map((item) => item.msg)
      .filter(Boolean)
    if (messages.length > 0) {
      return messages.join('. ')
    }
  }

  return fallback
}

export function validateEmail(email) {
  if (!email.trim()) {
    return 'Email is required.'
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
    return 'Enter a valid email address.'
  }
  return null
}

export function validatePassword(password, { minLength = 1 } = {}) {
  if (!password) {
    return 'Password is required.'
  }
  if (password.length > 72) {
    return 'Password must be at most 72 characters.'
  }
  if (password.length < minLength) {
    return `Password must be at least ${minLength} characters.`
  }
  return null
}

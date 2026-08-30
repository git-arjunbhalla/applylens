import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'
import api, { resetAuthClientState } from '../services/api'

const originalAdapter = api.defaults.adapter

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

window.ResizeObserver = window.ResizeObserver || ResizeObserverStub

window.matchMedia = (query) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener() {},
  removeListener() {},
  addEventListener() {},
  removeEventListener() {},
  dispatchEvent() {
    return false
  },
})

afterEach(() => {
  cleanup()
  api.defaults.adapter = originalAdapter
  resetAuthClientState()
  window.localStorage.clear()
  document.documentElement.classList.remove('dark')
  delete document.documentElement.dataset.theme
  document.documentElement.style.colorScheme = ''
})

import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'
import api, { resetAuthClientState } from '../services/api'

const originalAdapter = api.defaults.adapter

afterEach(() => {
  cleanup()
  api.defaults.adapter = originalAdapter
  resetAuthClientState()
  window.localStorage.clear()
})

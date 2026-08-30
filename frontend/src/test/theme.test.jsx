import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import App from '../App'
import { THEME_STORAGE_KEY } from '../context/ThemeContext'
import { installApiMock } from './mockApi'

describe('theme preference', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('defaults to the system theme and persists a user choice', async () => {
    const user = userEvent.setup()
    installApiMock({})
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: /log in/i })).toBeInTheDocument()
    expect(document.documentElement.classList.contains('dark')).toBe(false)

    await user.click(screen.getByRole('button', { name: /switch to dark theme/i }))

    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(window.localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')
    expect(screen.getByRole('button', { name: /switch to light theme/i })).toBeInTheDocument()
  })

  it('restores a stored dark preference', async () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, 'dark')
    installApiMock({})
    render(
      <MemoryRouter initialEntries={['/login']}>
        <App />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: /log in/i })).toBeInTheDocument()
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})

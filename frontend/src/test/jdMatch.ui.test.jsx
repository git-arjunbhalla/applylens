import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import App from '../App'
import { installApiMock, sampleUser, tokenPayload } from './mockApi'

const sampleMatch = {
  matched_keywords: ['Python', 'FastAPI', 'PostgreSQL'],
  missing_keywords: ['Docker', 'Redis'],
  relevant_skills: ['Python', 'FastAPI', 'SQL'],
  important_requirements: [
    'Backend development experience',
    'REST API development',
    'PostgreSQL experience',
  ],
  match_score: 78,
}

function renderJdMatch(extraHandlers = {}) {
  window.localStorage.setItem('applylens.refresh_token', 'refresh-token')
  const mock = installApiMock({
    'post /api/v1/auth/refresh': () => ({ status: 200, data: tokenPayload() }),
    'get /api/v1/auth/me': () => ({ status: 200, data: sampleUser }),
    ...extraHandlers,
  })
  render(
    <MemoryRouter initialEntries={['/jd-match']}>
      <App />
    </MemoryRouter>,
  )
  return mock
}

describe('job description match', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('shows an empty state before matching', async () => {
    renderJdMatch()

    expect(await screen.findByRole('heading', { name: 'Job description match' })).toBeInTheDocument()
    expect(screen.getByText('No match yet')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'JD match' })).toBeInTheDocument()
  })

  it('validates empty resume and job description before calling the API', async () => {
    const user = userEvent.setup()
    const { requests } = renderJdMatch()

    expect(await screen.findByRole('heading', { name: 'Job description match' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Match keywords' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Resume and job description are required.',
    )
    expect(requests.some((request) => request.path === '/api/v1/ai/jd-match')).toBe(false)
  })

  it('submits resume and job description and displays structured results', async () => {
    const user = userEvent.setup()
    const { requests } = renderJdMatch({
      'post /api/v1/ai/jd-match': () => ({
        status: 200,
        data: sampleMatch,
      }),
    })

    expect(await screen.findByRole('heading', { name: 'Job description match' })).toBeInTheDocument()
    await user.type(screen.getByLabelText('Resume'), 'Python developer with FastAPI.')
    await user.type(screen.getByLabelText('Job description'), 'Need Python, FastAPI, Docker, and Redis.')
    await user.click(screen.getByRole('button', { name: 'Match keywords' }))

    expect(await screen.findByText('78 / 100')).toBeInTheDocument()
    expect(screen.getAllByText('Python').length).toBeGreaterThan(0)
    expect(screen.getByText('Docker')).toBeInTheDocument()
    expect(screen.getByText('Redis')).toBeInTheDocument()
    expect(screen.getByText('SQL')).toBeInTheDocument()
    expect(screen.getByText('Backend development experience')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Matched keywords' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Missing keywords' })).toBeInTheDocument()
    expect(screen.queryByText('No match yet')).not.toBeInTheDocument()
    expect(screen.queryByText(/api[_-]?key/i)).not.toBeInTheDocument()

    const matchRequest = requests.find((request) => request.path === '/api/v1/ai/jd-match')
    expect(matchRequest).toBeTruthy()
    expect(matchRequest.method).toBe('post')
    expect(matchRequest.data).toEqual({
      resume_text: 'Python developer with FastAPI.',
      job_description: 'Need Python, FastAPI, Docker, and Redis.',
    })
  })

  it('shows a loading state while the match request is in flight', async () => {
    const user = userEvent.setup()
    let resolveRequest
    const pending = new Promise((resolve) => {
      resolveRequest = resolve
    })

    renderJdMatch({
      'post /api/v1/ai/jd-match': async () => {
        await pending
        return { status: 200, data: sampleMatch }
      },
    })

    expect(await screen.findByRole('heading', { name: 'Job description match' })).toBeInTheDocument()
    await user.type(screen.getByLabelText('Resume'), 'Resume text')
    await user.type(screen.getByLabelText('Job description'), 'Job text')
    await user.click(screen.getByRole('button', { name: 'Match keywords' }))

    expect(await screen.findByText('Matching resume and job description…')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Matching…' })).toBeDisabled()

    resolveRequest()

    expect(await screen.findByText('78 / 100')).toBeInTheDocument()
  })

  it('shows an error state when matching fails and allows retry', async () => {
    const user = userEvent.setup()
    let failOnce = true
    renderJdMatch({
      'post /api/v1/ai/jd-match': () => {
        if (failOnce) {
          failOnce = false
          return {
            status: 502,
            data: { detail: 'The AI provider request failed.' },
          }
        }
        return { status: 200, data: sampleMatch }
      },
    })

    expect(await screen.findByRole('heading', { name: 'Job description match' })).toBeInTheDocument()
    await user.type(screen.getByLabelText('Resume'), 'Resume text')
    await user.type(screen.getByLabelText('Job description'), 'Job text')
    await user.click(screen.getByRole('button', { name: 'Match keywords' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The AI provider request failed.')
    expect(screen.queryByText('78 / 100')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText('78 / 100')).toBeInTheDocument()
  })
})

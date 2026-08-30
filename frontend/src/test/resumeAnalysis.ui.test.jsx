import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import App from '../App'
import { installApiMock, sampleUser, tokenPayload } from './mockApi'

const sampleAnalysis = {
  match_score: 72,
  matching_skills: ['Python', 'FastAPI'],
  missing_skills: ['React'],
  strengths: ['Backend experience'],
  weaknesses: ['No frontend evidence'],
  recommendations: ['Mention React if you have it'],
}

function renderAnalyze(extraHandlers = {}) {
  window.localStorage.setItem('applylens.refresh_token', 'refresh-token')
  const mock = installApiMock({
    'post /api/v1/auth/refresh': () => ({ status: 200, data: tokenPayload() }),
    'get /api/v1/auth/me': () => ({ status: 200, data: sampleUser }),
    ...extraHandlers,
  })
  render(
    <MemoryRouter initialEntries={['/analyze']}>
      <App />
    </MemoryRouter>,
  )
  return mock
}

describe('resume analysis', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('shows an empty state before analysis', async () => {
    renderAnalyze()

    expect(await screen.findByRole('heading', { name: 'Resume analysis' })).toBeInTheDocument()
    expect(screen.getByText('No analysis yet')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Analyze' })).toBeInTheDocument()
  })

  it('validates empty resume and job description before calling the API', async () => {
    const user = userEvent.setup()
    const { requests } = renderAnalyze()

    expect(await screen.findByRole('heading', { name: 'Resume analysis' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Analyze' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Resume and job description are required.',
    )
    expect(
      requests.some((request) => request.path === '/api/v1/ai/resume-analysis'),
    ).toBe(false)
  })

  it('submits resume and job description and displays structured results', async () => {
    const user = userEvent.setup()
    const { requests } = renderAnalyze({
      'post /api/v1/ai/resume-analysis': () => ({
        status: 200,
        data: sampleAnalysis,
      }),
    })

    expect(await screen.findByRole('heading', { name: 'Resume analysis' })).toBeInTheDocument()
    await user.type(screen.getByLabelText('Resume'), 'Python developer with FastAPI.')
    await user.type(screen.getByLabelText('Job description'), 'Need Python, FastAPI, and React.')
    await user.click(screen.getByRole('button', { name: 'Analyze' }))

    expect(await screen.findByText('72 / 100')).toBeInTheDocument()
    expect(screen.getByText('Python')).toBeInTheDocument()
    expect(screen.getByText('FastAPI')).toBeInTheDocument()
    expect(screen.getByText('React')).toBeInTheDocument()
    expect(screen.getByText('Backend experience')).toBeInTheDocument()
    expect(screen.getByText('No frontend evidence')).toBeInTheDocument()
    expect(screen.getByText('Mention React if you have it')).toBeInTheDocument()
    expect(screen.queryByText('No analysis yet')).not.toBeInTheDocument()
    expect(screen.queryByText(/api[_-]?key/i)).not.toBeInTheDocument()

    const analysisRequest = requests.find((request) => request.path === '/api/v1/ai/resume-analysis')
    expect(analysisRequest).toBeTruthy()
    expect(analysisRequest.method).toBe('post')
    expect(analysisRequest.data).toEqual({
      resume_text: 'Python developer with FastAPI.',
      job_description: 'Need Python, FastAPI, and React.',
    })
  })

  it('shows a loading state while the analysis request is in flight', async () => {
    const user = userEvent.setup()
    let resolveRequest
    const pending = new Promise((resolve) => {
      resolveRequest = resolve
    })

    renderAnalyze({
      'post /api/v1/ai/resume-analysis': async () => {
        await pending
        return { status: 200, data: sampleAnalysis }
      },
    })

    expect(await screen.findByRole('heading', { name: 'Resume analysis' })).toBeInTheDocument()
    await user.type(screen.getByLabelText('Resume'), 'Resume text')
    await user.type(screen.getByLabelText('Job description'), 'Job text')
    await user.click(screen.getByRole('button', { name: 'Analyze' }))

    expect(await screen.findByText('Analyzing resume and job description…')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Analyzing…' })).toBeDisabled()

    resolveRequest()

    expect(await screen.findByText('72 / 100')).toBeInTheDocument()
  })

  it('shows an error state when analysis fails', async () => {
    const user = userEvent.setup()
    renderAnalyze({
      'post /api/v1/ai/resume-analysis': () => ({
        status: 502,
        data: { detail: 'The AI provider request failed.' },
      }),
    })

    expect(await screen.findByRole('heading', { name: 'Resume analysis' })).toBeInTheDocument()
    await user.type(screen.getByLabelText('Resume'), 'Resume text')
    await user.type(screen.getByLabelText('Job description'), 'Job text')
    await user.click(screen.getByRole('button', { name: 'Analyze' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The AI provider request failed.')
    expect(screen.queryByText('72 / 100')).not.toBeInTheDocument()
  })
})

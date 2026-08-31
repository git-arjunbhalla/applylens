import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import App from '../App'
import { RESUME_PDF_MAX_BYTES } from '../services/ai'
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

function pdfFile(name = 'resume.pdf') {
  return new File(['%PDF-1.4 resume'], name, { type: 'application/pdf' })
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

async function fillValidMatchForm(user) {
  await user.upload(screen.getByLabelText('Resume'), pdfFile())
  await user.type(screen.getByLabelText('Job description'), 'Need Python, FastAPI, Docker, and Redis.')
}

describe('job description match', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('shows an empty state and a PDF upload control', async () => {
    renderJdMatch()

    expect(await screen.findByRole('heading', { name: 'Job description match' })).toBeInTheDocument()
    expect(screen.getByText('No match yet')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'JD match' })).toBeInTheDocument()

    const resumeInput = screen.getByLabelText('Resume')
    expect(resumeInput).toHaveAttribute('type', 'file')
    expect(resumeInput).toHaveAttribute('accept', 'application/pdf')
    expect(screen.getByText('Choose a PDF resume.')).toBeInTheDocument()
    expect(screen.getByLabelText('Job description')).toBeInTheDocument()
  })

  it('validates missing PDF and job description before calling the API', async () => {
    const user = userEvent.setup()
    const { requests } = renderJdMatch()

    expect(await screen.findByRole('heading', { name: 'Job description match' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Match Resume' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Upload a resume PDF and enter a job description.',
    )
    expect(requests.some((request) => request.path === '/api/v1/ai/jd-match')).toBe(false)
  })

  it('rejects a non-PDF file before calling the API', async () => {
    const user = userEvent.setup()
    const { requests } = renderJdMatch()

    expect(await screen.findByRole('heading', { name: 'Job description match' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Resume'), {
      target: { files: [new File(['plain resume'], 'resume.txt', { type: 'text/plain' })] },
    })
    await user.type(screen.getByLabelText('Job description'), 'Need a backend engineer.')
    await user.click(screen.getByRole('button', { name: 'Match Resume' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The resume must be a PDF file.')
    expect(requests.some((request) => request.path === '/api/v1/ai/jd-match')).toBe(false)
  })

  it('rejects an oversized PDF before calling the API', async () => {
    const user = userEvent.setup()
    const { requests } = renderJdMatch()
    const oversized = new File(['x'.repeat(RESUME_PDF_MAX_BYTES + 1)], 'resume.pdf', {
      type: 'application/pdf',
    })

    expect(await screen.findByRole('heading', { name: 'Job description match' })).toBeInTheDocument()
    await user.upload(screen.getByLabelText('Resume'), oversized)
    await user.type(screen.getByLabelText('Job description'), 'Need a backend engineer.')
    await user.click(screen.getByRole('button', { name: 'Match Resume' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The resume PDF must be 5 MB or smaller.',
    )
    expect(requests.some((request) => request.path === '/api/v1/ai/jd-match')).toBe(false)
  })

  it('shows the selected PDF filename', async () => {
    const user = userEvent.setup()
    renderJdMatch()

    expect(await screen.findByRole('heading', { name: 'Job description match' })).toBeInTheDocument()
    await user.upload(screen.getByLabelText('Resume'), pdfFile('my-resume.pdf'))

    expect(screen.getByText('Selected file: my-resume.pdf')).toBeInTheDocument()
  })

  it('submits the PDF and job description as FormData and displays results', async () => {
    const user = userEvent.setup()
    const { requests } = renderJdMatch({
      'post /api/v1/ai/jd-match': () => ({
        status: 200,
        data: sampleMatch,
      }),
    })

    expect(await screen.findByRole('heading', { name: 'Job description match' })).toBeInTheDocument()
    await fillValidMatchForm(user)
    await user.click(screen.getByRole('button', { name: 'Match Resume' }))

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
    expect(matchRequest.data).toBeInstanceOf(FormData)
    expect(matchRequest.data.get('job_description')).toBe(
      'Need Python, FastAPI, Docker, and Redis.',
    )
    const uploaded = matchRequest.data.get('resume')
    expect(uploaded).toBeInstanceOf(File)
    expect(uploaded.name).toBe('resume.pdf')
    expect(uploaded.type).toBe('application/pdf')
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
    await user.upload(screen.getByLabelText('Resume'), pdfFile())
    await user.type(screen.getByLabelText('Job description'), 'Job text')
    await user.click(screen.getByRole('button', { name: 'Match Resume' }))

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
    await user.upload(screen.getByLabelText('Resume'), pdfFile())
    await user.type(screen.getByLabelText('Job description'), 'Job text')
    await user.click(screen.getByRole('button', { name: 'Match Resume' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The AI provider request failed.')
    expect(screen.queryByText('78 / 100')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText('78 / 100')).toBeInTheDocument()
  })
})

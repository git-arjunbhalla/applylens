import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { RESUME_PDF_MAX_BYTES } from '../services/ai'
import { installApiMock, sampleUser, tokenPayload } from './mockApi'

const sampleLetter = {
  cover_letter:
    'Dear Hiring Manager,\n\nI am applying for the Backend Engineer role at Acme Labs.\n\nSincerely,\nJane Doe',
}

function pdfFile(name = 'resume.pdf') {
  return new File(['%PDF-1.4 resume'], name, { type: 'application/pdf' })
}

function renderCoverLetter(extraHandlers = {}) {
  window.localStorage.setItem('applylens.refresh_token', 'refresh-token')
  const mock = installApiMock({
    'post /api/v1/auth/refresh': () => ({ status: 200, data: tokenPayload() }),
    'get /api/v1/auth/me': () => ({ status: 200, data: sampleUser }),
    ...extraHandlers,
  })
  render(
    <MemoryRouter initialEntries={['/cover-letter']}>
      <App />
    </MemoryRouter>,
  )
  return mock
}

async function fillValidForm(user) {
  await user.upload(screen.getByLabelText('Resume'), pdfFile())
  await user.type(screen.getByLabelText('Company'), 'Acme Labs')
  await user.type(screen.getByLabelText('Role'), 'Backend Engineer')
  await user.type(screen.getByLabelText('Job description'), 'Need Python and FastAPI.')
}

describe('cover letter', () => {
  beforeEach(() => {
    window.localStorage.clear()
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('shows an empty state and the required form fields', async () => {
    renderCoverLetter()

    expect(await screen.findByRole('heading', { name: 'Cover letter' })).toBeInTheDocument()
    expect(screen.getByText('No cover letter yet')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Cover letter' })).toBeInTheDocument()

    const resumeInput = screen.getByLabelText('Resume')
    expect(resumeInput).toHaveAttribute('type', 'file')
    expect(resumeInput).toHaveAttribute('accept', 'application/pdf')
    expect(screen.getByText('Choose a PDF resume.')).toBeInTheDocument()
    expect(screen.getByLabelText('Company')).toBeInTheDocument()
    expect(screen.getByLabelText('Role')).toBeInTheDocument()
    expect(screen.getByLabelText('Job description')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Generate Cover Letter' })).toBeInTheDocument()
  })

  it('validates missing required fields before calling the API', async () => {
    const user = userEvent.setup()
    const { requests } = renderCoverLetter()

    expect(await screen.findByRole('heading', { name: 'Cover letter' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Generate Cover Letter' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Upload a resume PDF and enter company, role, and job description.',
    )
    expect(requests.some((request) => request.path === '/api/v1/ai/cover-letter')).toBe(false)
  })

  it('rejects a non-PDF file before calling the API', async () => {
    const user = userEvent.setup()
    const { requests } = renderCoverLetter()

    expect(await screen.findByRole('heading', { name: 'Cover letter' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Resume'), {
      target: { files: [new File(['plain resume'], 'resume.txt', { type: 'text/plain' })] },
    })
    await user.type(screen.getByLabelText('Company'), 'Acme Labs')
    await user.type(screen.getByLabelText('Role'), 'Backend Engineer')
    await user.type(screen.getByLabelText('Job description'), 'Need a backend engineer.')
    await user.click(screen.getByRole('button', { name: 'Generate Cover Letter' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The resume must be a PDF file.')
    expect(requests.some((request) => request.path === '/api/v1/ai/cover-letter')).toBe(false)
  })

  it('rejects an oversized PDF before calling the API', async () => {
    const user = userEvent.setup()
    const { requests } = renderCoverLetter()
    const oversized = new File(['x'.repeat(RESUME_PDF_MAX_BYTES + 1)], 'resume.pdf', {
      type: 'application/pdf',
    })

    expect(await screen.findByRole('heading', { name: 'Cover letter' })).toBeInTheDocument()
    await user.upload(screen.getByLabelText('Resume'), oversized)
    await user.type(screen.getByLabelText('Company'), 'Acme Labs')
    await user.type(screen.getByLabelText('Role'), 'Backend Engineer')
    await user.type(screen.getByLabelText('Job description'), 'Need a backend engineer.')
    await user.click(screen.getByRole('button', { name: 'Generate Cover Letter' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The resume PDF must be 5 MB or smaller.',
    )
    expect(requests.some((request) => request.path === '/api/v1/ai/cover-letter')).toBe(false)
  })

  it('shows the selected PDF filename', async () => {
    const user = userEvent.setup()
    renderCoverLetter()

    expect(await screen.findByRole('heading', { name: 'Cover letter' })).toBeInTheDocument()
    await user.upload(screen.getByLabelText('Resume'), pdfFile('my-resume.pdf'))

    expect(screen.getByText('Selected file: my-resume.pdf')).toBeInTheDocument()
  })

  it('submits FormData and displays the generated letter', async () => {
    const user = userEvent.setup()
    const { requests } = renderCoverLetter({
      'post /api/v1/ai/cover-letter': () => ({
        status: 200,
        data: sampleLetter,
      }),
    })

    expect(await screen.findByRole('heading', { name: 'Cover letter' })).toBeInTheDocument()
    await fillValidForm(user)
    await user.click(screen.getByRole('button', { name: 'Generate Cover Letter' }))

    expect(await screen.findByText(/I am applying for the Backend Engineer role at Acme Labs/)).toBeInTheDocument()
    expect(screen.getByText(/AI-generated draft/)).toBeInTheDocument()
    expect(screen.queryByText('No cover letter yet')).not.toBeInTheDocument()
    expect(screen.queryByText(/api[_-]?key/i)).not.toBeInTheDocument()

    const request = requests.find((item) => item.path === '/api/v1/ai/cover-letter')
    expect(request).toBeTruthy()
    expect(request.method).toBe('post')
    expect(request.data).toBeInstanceOf(FormData)
    expect(request.data.get('company')).toBe('Acme Labs')
    expect(request.data.get('role')).toBe('Backend Engineer')
    expect(request.data.get('job_description')).toBe('Need Python and FastAPI.')
    const uploaded = request.data.get('resume')
    expect(uploaded).toBeInstanceOf(File)
    expect(uploaded.name).toBe('resume.pdf')
    expect(uploaded.type).toBe('application/pdf')
  })

  it('shows a loading state while generation is in flight', async () => {
    const user = userEvent.setup()
    let resolveRequest
    const pending = new Promise((resolve) => {
      resolveRequest = resolve
    })

    renderCoverLetter({
      'post /api/v1/ai/cover-letter': async () => {
        await pending
        return { status: 200, data: sampleLetter }
      },
    })

    expect(await screen.findByRole('heading', { name: 'Cover letter' })).toBeInTheDocument()
    await fillValidForm(user)
    await user.click(screen.getByRole('button', { name: 'Generate Cover Letter' }))

    expect(await screen.findByText('Generating cover letter…')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Generating…' })).toBeDisabled()

    resolveRequest()

    expect(await screen.findByText(/I am applying for the Backend Engineer role at Acme Labs/)).toBeInTheDocument()
  })

  it('copies the generated letter and shows Copied feedback', async () => {
    const user = userEvent.setup()
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', {
      ...navigator,
      clipboard: { writeText },
    })

    renderCoverLetter({
      'post /api/v1/ai/cover-letter': () => ({
        status: 200,
        data: sampleLetter,
      }),
    })

    expect(await screen.findByRole('heading', { name: 'Cover letter' })).toBeInTheDocument()
    await fillValidForm(user)
    await user.click(screen.getByRole('button', { name: 'Generate Cover Letter' }))

    expect(await screen.findByRole('button', { name: 'Copy' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Copy' }))

    expect(writeText).toHaveBeenCalledWith(sampleLetter.cover_letter)
    expect(await screen.findByRole('button', { name: 'Copied' })).toBeInTheDocument()
  })

  it('shows an error state when generation fails and allows retry', async () => {
    const user = userEvent.setup()
    let failOnce = true
    renderCoverLetter({
      'post /api/v1/ai/cover-letter': () => {
        if (failOnce) {
          failOnce = false
          return {
            status: 502,
            data: { detail: 'The AI provider request failed.' },
          }
        }
        return { status: 200, data: sampleLetter }
      },
    })

    expect(await screen.findByRole('heading', { name: 'Cover letter' })).toBeInTheDocument()
    await fillValidForm(user)
    await user.click(screen.getByRole('button', { name: 'Generate Cover Letter' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The AI provider request failed.')
    expect(screen.queryByText(/I am applying for the Backend Engineer role/)).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText(/I am applying for the Backend Engineer role at Acme Labs/)).toBeInTheDocument()
  })

  it('shows a safe 429 rate-limit message', async () => {
    const user = userEvent.setup()
    renderCoverLetter({
      'post /api/v1/ai/cover-letter': () => ({
        status: 429,
        data: { detail: 'AI request limit exceeded. Please try again later.' },
      }),
    })

    expect(await screen.findByRole('heading', { name: 'Cover letter' })).toBeInTheDocument()
    await fillValidForm(user)
    await user.click(screen.getByRole('button', { name: 'Generate Cover Letter' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'AI request limit exceeded. Please try again later.',
    )
    expect(screen.queryByText(/redis/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/I am applying for the Backend Engineer role/)).not.toBeInTheDocument()
  })
})

import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import App from '../App'
import { RESUME_PDF_MAX_BYTES } from '../services/ai'
import { installApiMock, sampleUser, tokenPayload } from './mockApi'

const sampleAnalysis = {
  ats_score: 78,
  score_breakdown: {
    ats_compatibility: 80,
    content_strength: 74,
    keyword_optimization: 70,
    resume_structure: 82,
    achievement_quality: 68,
  },
  strengths: ['Clear backend stack listed'],
  issues: ['Few measurable outcomes'],
  missing_sections: ['Professional summary'],
  detected_skills: ['Python', 'FastAPI'],
  keyword_suggestions: ['REST APIs'],
  improvement_suggestions: ['Add quantified results'],
  rewrite_suggestions: [
    {
      original: 'Worked on backend services',
      suggested: 'Built FastAPI services',
      reason: 'Names tools already present',
    },
  ],
  summary: 'Solid technical resume with room for more concrete achievements.',
}

function pdfFile(name = 'resume.pdf') {
  return new File(['%PDF-1.4 resume'], name, { type: 'application/pdf' })
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

describe('resume analyzer', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('shows an empty state and a PDF upload control', async () => {
    renderAnalyze()

    expect(await screen.findByRole('heading', { name: 'Resume Analyzer' })).toBeInTheDocument()
    expect(screen.getByText('See how ATS-friendly and effective your resume is.')).toBeInTheDocument()
    expect(screen.getByText('No analysis yet')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Analyze' })).toBeInTheDocument()
    expect(screen.queryByLabelText('Job description')).not.toBeInTheDocument()

    const resumeInput = screen.getByLabelText('Resume PDF')
    expect(resumeInput).toHaveAttribute('type', 'file')
    expect(resumeInput).toHaveAttribute('accept', 'application/pdf')
  })

  it('validates a missing PDF before calling the API', async () => {
    const user = userEvent.setup()
    const { requests } = renderAnalyze()

    expect(await screen.findByRole('heading', { name: 'Resume Analyzer' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Analyze Resume' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Upload a resume PDF to analyze.')
    expect(
      requests.some((request) => request.path === '/api/v1/ai/resume-analysis'),
    ).toBe(false)
  })

  it('rejects a non-PDF file before calling the API', async () => {
    const user = userEvent.setup()
    const { requests } = renderAnalyze()

    expect(await screen.findByRole('heading', { name: 'Resume Analyzer' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Resume PDF'), {
      target: { files: [new File(['plain resume'], 'resume.txt', { type: 'text/plain' })] },
    })
    await user.click(screen.getByRole('button', { name: 'Analyze Resume' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The resume must be a PDF file.')
    expect(
      requests.some((request) => request.path === '/api/v1/ai/resume-analysis'),
    ).toBe(false)
  })

  it('rejects an oversized PDF before calling the API', async () => {
    const user = userEvent.setup()
    const { requests } = renderAnalyze()
    const oversized = new File(['x'.repeat(RESUME_PDF_MAX_BYTES + 1)], 'resume.pdf', {
      type: 'application/pdf',
    })

    expect(await screen.findByRole('heading', { name: 'Resume Analyzer' })).toBeInTheDocument()
    await user.upload(screen.getByLabelText('Resume PDF'), oversized)
    await user.click(screen.getByRole('button', { name: 'Analyze Resume' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The resume PDF must be 5 MB or smaller.',
    )
    expect(
      requests.some((request) => request.path === '/api/v1/ai/resume-analysis'),
    ).toBe(false)
  })

  it('submits the PDF as FormData and displays ATS results', async () => {
    const user = userEvent.setup()
    const { requests } = renderAnalyze({
      'post /api/v1/ai/resume-analysis': () => ({
        status: 200,
        data: sampleAnalysis,
      }),
    })

    expect(await screen.findByRole('heading', { name: 'Resume Analyzer' })).toBeInTheDocument()
    await user.upload(screen.getByLabelText('Resume PDF'), pdfFile())
    expect(screen.getByText('Selected file: resume.pdf')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Analyze Resume' }))

    expect(await screen.findByText('78 / 100')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Estimated resume quality based on the content we could extract from your PDF. This is not a hiring decision.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('ATS Compatibility')).toBeInTheDocument()
    expect(screen.getByText('Content Strength')).toBeInTheDocument()
    expect(screen.getByText('Keyword Optimization')).toBeInTheDocument()
    expect(screen.getByText('Resume Structure')).toBeInTheDocument()
    expect(screen.getByText('Achievement Quality')).toBeInTheDocument()
    expect(screen.getByText('Clear backend stack listed')).toBeInTheDocument()
    expect(screen.getByText('Few measurable outcomes')).toBeInTheDocument()
    expect(screen.getByText('Add quantified results')).toBeInTheDocument()
    expect(screen.getByText('Worked on backend services')).toBeInTheDocument()
    expect(screen.getByText('Built FastAPI services')).toBeInTheDocument()
    expect(screen.queryByText('No analysis yet')).not.toBeInTheDocument()
    expect(screen.queryByText(/api[_-]?key/i)).not.toBeInTheDocument()

    const analysisRequest = requests.find((request) => request.path === '/api/v1/ai/resume-analysis')
    expect(analysisRequest).toBeTruthy()
    expect(analysisRequest.method).toBe('post')
    expect(analysisRequest.data).toBeInstanceOf(FormData)
    const uploaded = analysisRequest.data.get('resume')
    expect(uploaded).toBeInstanceOf(File)
    expect(uploaded.name).toBe('resume.pdf')
    expect(analysisRequest.data.get('job_description')).toBeNull()
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

    expect(await screen.findByRole('heading', { name: 'Resume Analyzer' })).toBeInTheDocument()
    await user.upload(screen.getByLabelText('Resume PDF'), pdfFile())
    await user.click(screen.getByRole('button', { name: 'Analyze Resume' }))

    expect(await screen.findByText('Reviewing resume quality…')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Analyzing…' })).toBeDisabled()

    resolveRequest()

    expect(await screen.findByText('78 / 100')).toBeInTheDocument()
  })

  it('shows an error state when analysis fails and allows retry', async () => {
    const user = userEvent.setup()
    let failOnce = true
    renderAnalyze({
      'post /api/v1/ai/resume-analysis': () => {
        if (failOnce) {
          failOnce = false
          return {
            status: 502,
            data: { detail: 'The AI provider request failed.' },
          }
        }
        return { status: 200, data: sampleAnalysis }
      },
    })

    expect(await screen.findByRole('heading', { name: 'Resume Analyzer' })).toBeInTheDocument()
    await user.upload(screen.getByLabelText('Resume PDF'), pdfFile())
    await user.click(screen.getByRole('button', { name: 'Analyze Resume' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The AI provider request failed.')
    expect(screen.queryByText('78 / 100')).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Try again' }))

    expect(await screen.findByText('78 / 100')).toBeInTheDocument()
  })

  it('shows a safe 429 rate-limit message', async () => {
    const user = userEvent.setup()
    renderAnalyze({
      'post /api/v1/ai/resume-analysis': () => ({
        status: 429,
        data: { detail: 'AI request limit exceeded. Please try again later.' },
      }),
    })

    expect(await screen.findByRole('heading', { name: 'Resume Analyzer' })).toBeInTheDocument()
    await user.upload(screen.getByLabelText('Resume PDF'), pdfFile())
    await user.click(screen.getByRole('button', { name: 'Analyze Resume' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'AI request limit exceeded. Please try again later.',
    )
    expect(screen.queryByText(/redis/i)).not.toBeInTheDocument()
    expect(screen.queryByText('78 / 100')).not.toBeInTheDocument()
  })
})

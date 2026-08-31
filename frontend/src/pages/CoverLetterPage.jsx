import { useState } from 'react'
import Alert from '../components/Alert'
import Button from '../components/Button'
import Card from '../components/Card'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import Field, { inputClass } from '../components/Field'
import LoadingState from '../components/LoadingState'
import Page, { PageHeader } from '../components/Page'
import { RESUME_PDF_MAX_BYTES, generateCoverLetter } from '../services/ai'
import { getApiErrorMessage } from '../services/authErrors'

function isPdfFile(file) {
  return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
}

function CoverLetterPage() {
  const [resumeFile, setResumeFile] = useState(null)
  const [company, setCompany] = useState('')
  const [role, setRole] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [formError, setFormError] = useState('')
  const [result, setResult] = useState(null)
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)

  function handleResumeChange(event) {
    const file = event.target.files?.[0] ?? null
    setResumeFile(file)
    setFormError('')
  }

  async function runGenerate() {
    const companyName = company.trim()
    const roleTitle = role.trim()
    const job = jobDescription.trim()
    if (!resumeFile || !companyName || !roleTitle || !job) {
      setFormError('Upload a resume PDF and enter company, role, and job description.')
      return
    }
    if (!isPdfFile(resumeFile)) {
      setFormError('The resume must be a PDF file.')
      return
    }
    if (resumeFile.size > RESUME_PDF_MAX_BYTES) {
      setFormError('The resume PDF must be 5 MB or smaller.')
      return
    }

    setFormError('')
    setError('')
    setCopied(false)
    setStatus('loading')
    try {
      const letter = await generateCoverLetter({
        resume: resumeFile,
        company: companyName,
        role: roleTitle,
        job_description: job,
      })
      setResult(letter)
      setStatus('ready')
    } catch (err) {
      setResult(null)
      setError(getApiErrorMessage(err, 'Unable to generate a cover letter.'))
      setStatus('error')
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    void runGenerate()
  }

  async function copyLetter() {
    if (!result?.cover_letter) {
      return
    }
    try {
      await navigator.clipboard.writeText(result.cover_letter)
      setCopied(true)
    } catch {
      setCopied(false)
      setFormError('Unable to copy the cover letter.')
    }
  }

  return (
    <Page>
      <PageHeader
        title="Cover letter"
        description="Upload a resume PDF and generate an AI draft tailored to a company, role, and job description. Review it for accuracy before you send it."
      />

      <Card className="mt-8 p-4 sm:p-6">
        <form className="space-y-4" onSubmit={handleSubmit} noValidate>
          {formError ? <Alert>{formError}</Alert> : null}

          <div>
            <Field label="Resume">
              <input
                className={inputClass}
                type="file"
                name="resume"
                accept="application/pdf"
                onChange={handleResumeChange}
              />
            </Field>
            <p className="mt-2 text-sm text-muted">
              {resumeFile ? `Selected file: ${resumeFile.name}` : 'Choose a PDF resume.'}
            </p>
          </div>

          <Field label="Company">
            <input
              className={inputClass}
              type="text"
              name="company"
              value={company}
              onChange={(event) => setCompany(event.target.value)}
            />
          </Field>

          <Field label="Role">
            <input
              className={inputClass}
              type="text"
              name="role"
              value={role}
              onChange={(event) => setRole(event.target.value)}
            />
          </Field>

          <Field label="Job description">
            <textarea
              className={inputClass}
              name="job_description"
              rows={10}
              value={jobDescription}
              onChange={(event) => setJobDescription(event.target.value)}
            />
          </Field>

          <Button type="submit" disabled={status === 'loading'}>
            {status === 'loading' ? 'Generating…' : 'Generate Cover Letter'}
          </Button>
        </form>
      </Card>

      <div className="mt-8">
        {status === 'idle' ? (
          <EmptyState
            title="No cover letter yet"
            message="Upload a resume PDF, enter the company, role, and job description, then generate a draft."
          />
        ) : null}

        {status === 'loading' ? <LoadingState message="Generating cover letter…" /> : null}

        {status === 'error' ? <ErrorState message={error} onRetry={() => void runGenerate()} /> : null}

        {status === 'ready' && result ? (
          <Card className="p-4 sm:p-6">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="font-display text-lg font-semibold text-ink">Generated draft</h2>
                <p className="mt-1 text-sm text-muted">
                  This is an AI-generated draft based only on the supplied resume and job description.
                  Review it for accuracy before use. It is not guaranteed to be factually accurate.
                </p>
              </div>
              <Button type="button" variant="secondary" onClick={() => void copyLetter()}>
                {copied ? 'Copied' : 'Copy'}
              </Button>
            </div>
            <pre className="mt-4 whitespace-pre-wrap font-sans text-ink">{result.cover_letter}</pre>
          </Card>
        ) : null}
      </div>
    </Page>
  )
}

export default CoverLetterPage

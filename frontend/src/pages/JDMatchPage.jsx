import { useState } from 'react'
import Alert from '../components/Alert'
import Button from '../components/Button'
import Card from '../components/Card'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import Field, { inputClass } from '../components/Field'
import LoadingState from '../components/LoadingState'
import Page, { PageHeader } from '../components/Page'
import { RESUME_PDF_MAX_BYTES, matchJobDescription } from '../services/ai'
import { getApiErrorMessage } from '../services/authErrors'

function KeywordList({ title, items, emptyLabel, tone = 'matched' }) {
  const badgeClass =
    tone === 'missing'
      ? 'inline-flex rounded-full border border-line bg-canvas px-2.5 py-0.5 text-sm text-muted'
      : 'inline-flex rounded-full border border-line bg-accent-soft px-2.5 py-0.5 text-sm text-ink'

  return (
    <div>
      <h3 className="text-sm font-medium text-muted">{title}</h3>
      {items.length === 0 ? (
        <p className="mt-1 text-ink">{emptyLabel}</p>
      ) : (
        <ul className="mt-2 flex flex-wrap gap-2">
          {items.map((item, index) => (
            <li key={`${title}-${index}`} className={badgeClass}>
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function RequirementList({ items }) {
  return (
    <div>
      <h3 className="text-sm font-medium text-muted">Important requirements</h3>
      {items.length === 0 ? (
        <p className="mt-1 text-ink">None identified from the provided text.</p>
      ) : (
        <ul className="mt-1 list-disc space-y-1 pl-5 text-ink">
          {items.map((item, index) => (
            <li key={`requirement-${index}`}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

function isPdfFile(file) {
  return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
}

function JDMatchPage() {
  const [resumeFile, setResumeFile] = useState(null)
  const [jobDescription, setJobDescription] = useState('')
  const [formError, setFormError] = useState('')
  const [result, setResult] = useState(null)
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')

  function handleResumeChange(event) {
    const file = event.target.files?.[0] ?? null
    setResumeFile(file)
    setFormError('')
  }

  async function runMatch() {
    const job = jobDescription.trim()
    if (!resumeFile || !job) {
      setFormError('Upload a resume PDF and enter a job description.')
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
    setStatus('loading')
    try {
      const match = await matchJobDescription({
        resume: resumeFile,
        job_description: job,
      })
      setResult(match)
      setStatus('ready')
    } catch (err) {
      setResult(null)
      setError(getApiErrorMessage(err, 'Unable to match the job description.'))
      setStatus('error')
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    void runMatch()
  }

  return (
    <Page>
      <PageHeader
        title="Job description match"
        description="Upload a resume PDF and compare its keywords to a job description. The PDF is read on the server and is not stored."
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
            {status === 'loading' ? 'Matching…' : 'Match Resume'}
          </Button>
        </form>
      </Card>

      <div className="mt-8">
        {status === 'idle' ? (
          <EmptyState
            title="No match yet"
            message="Upload a resume PDF and paste a job description, then run the keyword comparison."
          />
        ) : null}

        {status === 'loading' ? <LoadingState message="Matching resume and job description…" /> : null}

        {status === 'error' ? <ErrorState message={error} onRetry={() => void runMatch()} /> : null}

        {status === 'ready' && result ? (
          <Card className="p-4 sm:p-6">
            <p className="text-sm text-muted">Match score</p>
            <p className="mt-1 font-display text-3xl font-semibold text-ink">{result.match_score} / 100</p>
            <p className="mt-2 text-sm text-muted">
              Keyword overlap based only on the supplied resume and job description. This is not a hiring decision.
            </p>
            <div className="mt-6 grid gap-6 sm:grid-cols-2">
              <KeywordList
                title="Matched keywords"
                items={result.matched_keywords}
                emptyLabel="None identified from the provided text."
              />
              <KeywordList
                title="Missing keywords"
                items={result.missing_keywords}
                emptyLabel="No missing keywords identified from the provided text."
                tone="missing"
              />
              <KeywordList
                title="Relevant skills"
                items={result.relevant_skills}
                emptyLabel="None identified from the provided text."
              />
            </div>
            <div className="mt-6">
              <RequirementList items={result.important_requirements} />
            </div>
          </Card>
        ) : null}
      </div>
    </Page>
  )
}

export default JDMatchPage

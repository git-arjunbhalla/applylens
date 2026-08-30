import { useState } from 'react'
import Alert from '../components/Alert'
import Button from '../components/Button'
import Card from '../components/Card'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import Field, { inputClass } from '../components/Field'
import LoadingState from '../components/LoadingState'
import Page, { PageHeader } from '../components/Page'
import { analyzeResume } from '../services/ai'
import { getApiErrorMessage } from '../services/authErrors'

function ResultList({ title, items }) {
  return (
    <div>
      <h3 className="text-sm font-medium text-muted">{title}</h3>
      {items.length === 0 ? (
        <p className="mt-1 text-ink">None identified from the provided text.</p>
      ) : (
        <ul className="mt-1 list-disc space-y-1 pl-5 text-ink">
          {items.map((item, index) => (
            <li key={`${title}-${index}`}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

function ResumeAnalysisPage() {
  const [resumeText, setResumeText] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [formError, setFormError] = useState('')
  const [result, setResult] = useState(null)
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    const resume = resumeText.trim()
    const job = jobDescription.trim()
    if (!resume || !job) {
      setFormError('Resume and job description are required.')
      return
    }

    setFormError('')
    setError('')
    setStatus('loading')
    try {
      const analysis = await analyzeResume({
        resume_text: resume,
        job_description: job,
      })
      setResult(analysis)
      setStatus('ready')
    } catch (err) {
      setResult(null)
      setError(getApiErrorMessage(err, 'Unable to analyze the resume.'))
      setStatus('error')
    }
  }

  return (
    <Page>
      <PageHeader
        title="Resume analysis"
        description="Compare resume text to a job description. Results use only the text you provide."
      />

      <Card className="mt-8 p-4 sm:p-6">
        <form className="space-y-4" onSubmit={handleSubmit} noValidate>
          {formError ? <Alert>{formError}</Alert> : null}

          <Field label="Resume">
            <textarea
              className={inputClass}
              name="resume_text"
              rows={10}
              value={resumeText}
              onChange={(event) => setResumeText(event.target.value)}
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
            {status === 'loading' ? 'Analyzing…' : 'Analyze'}
          </Button>
        </form>
      </Card>

      <div className="mt-8">
        {status === 'idle' ? (
          <EmptyState
            title="No analysis yet"
            message="Paste a resume and job description, then run the comparison."
          />
        ) : null}

        {status === 'loading' ? <LoadingState message="Analyzing resume and job description…" /> : null}

        {status === 'error' ? <ErrorState message={error} /> : null}

        {status === 'ready' && result ? (
          <Card className="p-4 sm:p-6">
            <p className="text-sm text-muted">Match score</p>
            <p className="mt-1 font-display text-3xl font-semibold text-ink">{result.match_score} / 100</p>
            <p className="mt-2 text-sm text-muted">
              Based only on the supplied resume and job description. This is not a hiring decision.
            </p>
            <div className="mt-6 grid gap-6 sm:grid-cols-2">
              <ResultList title="Matching skills" items={result.matching_skills} />
              <ResultList title="Missing skills" items={result.missing_skills} />
              <ResultList title="Strengths" items={result.strengths} />
              <ResultList title="Weaknesses" items={result.weaknesses} />
            </div>
            <div className="mt-6">
              <ResultList title="Recommendations" items={result.recommendations} />
            </div>
          </Card>
        ) : null}
      </div>
    </Page>
  )
}

export default ResumeAnalysisPage

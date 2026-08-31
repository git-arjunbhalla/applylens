import { useState } from 'react'
import Alert from '../components/Alert'
import Button from '../components/Button'
import Card from '../components/Card'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import Field, { inputClass } from '../components/Field'
import LoadingState from '../components/LoadingState'
import Page, { PageHeader } from '../components/Page'
import { RESUME_PDF_MAX_BYTES, analyzeResume } from '../services/ai'
import { getApiErrorMessage } from '../services/authErrors'

const BREAKDOWN_ITEMS = [
  { key: 'ats_compatibility', label: 'ATS Compatibility' },
  { key: 'content_strength', label: 'Content Strength' },
  { key: 'keyword_optimization', label: 'Keyword Optimization' },
  { key: 'resume_structure', label: 'Resume Structure' },
  { key: 'achievement_quality', label: 'Achievement Quality' },
]

function isPdfFile(file) {
  return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
}

function ResultList({ title, items, emptyLabel }) {
  return (
    <section>
      <h3 className="font-display text-lg font-medium text-ink">{title}</h3>
      {items.length === 0 ? (
        <p className="mt-2 text-muted">{emptyLabel}</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {items.map((item, index) => (
            <li
              key={`${title}-${index}`}
              className="rounded-md border border-line bg-canvas px-3 py-2 text-ink"
            >
              {item}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

function ResumeAnalysisPage() {
  const [resumeFile, setResumeFile] = useState(null)
  const [formError, setFormError] = useState('')
  const [result, setResult] = useState(null)
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')

  function handleResumeChange(event) {
    const file = event.target.files?.[0] ?? null
    setResumeFile(file)
    setFormError('')
  }

  async function runAnalysis() {
    if (!resumeFile) {
      setFormError('Upload a resume PDF to analyze.')
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
      const analysis = await analyzeResume({ resume: resumeFile })
      setResult(analysis)
      setStatus('ready')
    } catch (err) {
      setResult(null)
      setError(getApiErrorMessage(err, 'Unable to analyze the resume.'))
      setStatus('error')
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    void runAnalysis()
  }

  return (
    <Page>
      <PageHeader
        title="Resume Analyzer"
        description="See how ATS-friendly and effective your resume is."
      />

      <Card className="mt-8 p-4 sm:p-6">
        <form className="space-y-4" onSubmit={handleSubmit} noValidate>
          {formError ? <Alert>{formError}</Alert> : null}

          <div>
            <Field label="Resume PDF">
              <input
                className={inputClass}
                type="file"
                name="resume"
                accept="application/pdf"
                onChange={handleResumeChange}
              />
            </Field>
            <p className="mt-2 text-sm text-muted">
              {resumeFile
                ? `Selected file: ${resumeFile.name}`
                : 'Upload your resume only. No job description is used.'}
            </p>
          </div>

          <Button type="submit" disabled={status === 'loading'}>
            {status === 'loading' ? 'Analyzing…' : 'Analyze Resume'}
          </Button>
        </form>
      </Card>

      <div className="mt-8">
        {status === 'idle' ? (
          <EmptyState
            title="No analysis yet"
            message="Upload a resume PDF to get an ATS-oriented quality review. Use JD match when you want to compare against a job description."
          />
        ) : null}

        {status === 'loading' ? <LoadingState message="Reviewing resume quality…" /> : null}

        {status === 'error' ? <ErrorState message={error} onRetry={() => void runAnalysis()} /> : null}

        {status === 'ready' && result ? (
          <div className="space-y-6">
            <div className="overflow-hidden rounded-lg border border-line bg-surface">
              <div
                className="px-4 py-8 sm:px-6"
                style={{
                  background: 'linear-gradient(120deg, var(--al-hero-from), var(--al-hero-to))',
                }}
              >
                <p className="text-sm font-medium text-ink/80">ATS score</p>
                <p className="mt-1 font-display text-5xl font-semibold text-ink">
                  {result.ats_score} / 100
                </p>
                <p className="mt-3 max-w-2xl text-sm text-ink/80">
                  Estimated resume quality based on the content we could extract from your PDF. This
                  is not a hiring decision.
                </p>
              </div>
              {result.summary ? (
                <p className="border-t border-line px-4 py-4 text-ink sm:px-6">{result.summary}</p>
              ) : null}
            </div>

            <div>
              <h2 className="font-display text-xl font-medium text-ink">Score breakdown</h2>
              <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                {BREAKDOWN_ITEMS.map((item) => (
                  <Card key={item.key} className="px-3 py-4 text-center">
                    <p className="font-display text-2xl font-semibold text-ink">
                      {result.score_breakdown[item.key]}
                    </p>
                    <p className="mt-1 text-sm text-muted">{item.label}</p>
                  </Card>
                ))}
              </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
              <ResultList
                title="Strengths"
                items={result.strengths}
                emptyLabel="None identified from the extracted text."
              />
              <ResultList
                title="Issues to Fix"
                items={result.issues}
                emptyLabel="None identified from the extracted text."
              />
            </div>

            <ResultList
              title="Missing sections"
              items={result.missing_sections}
              emptyLabel="No missing sections identified from the extracted text."
            />
            <ResultList
              title="Detected skills"
              items={result.detected_skills}
              emptyLabel="No skills could be determined from the extracted text."
            />
            <ResultList
              title="Keyword Suggestions"
              items={result.keyword_suggestions}
              emptyLabel="No keyword suggestions from the extracted text."
            />
            <ResultList
              title="Improvement Suggestions"
              items={result.improvement_suggestions}
              emptyLabel="No improvement suggestions from the extracted text."
            />

            <section>
              <h3 className="font-display text-lg font-medium text-ink">Rewrite Suggestions</h3>
              {result.rewrite_suggestions.length === 0 ? (
                <p className="mt-2 text-muted">
                  No rewrite suggestions were supported by the extracted text.
                </p>
              ) : (
                <ul className="mt-3 space-y-3">
                  {result.rewrite_suggestions.map((item, index) => (
                    <li key={`rewrite-${index}`}>
                      <Card className="p-4">
                        <p className="text-sm text-muted">Original</p>
                        <p className="mt-1 text-ink">{item.original}</p>
                        <p className="mt-3 text-sm text-muted">Suggested</p>
                        <p className="mt-1 text-ink">{item.suggested}</p>
                        <p className="mt-3 text-sm text-muted">{item.reason}</p>
                      </Card>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        ) : null}
      </div>
    </Page>
  )
}

export default ResumeAnalysisPage

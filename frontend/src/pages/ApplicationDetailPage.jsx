import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import Alert from '../components/Alert'
import { buttonClass } from '../components/Button'
import ConfirmDialog from '../components/ConfirmDialog'
import ErrorState from '../components/ErrorState'
import InterviewSection from '../components/InterviewSection'
import LoadingState from '../components/LoadingState'
import Page from '../components/Page'
import StatusBadge from '../components/StatusBadge'
import { deleteApplication, getApplication } from '../services/applications'
import { getApiErrorMessage } from '../services/authErrors'
import { formatDate, formatDateTime } from '../utils/dates'

function DetailField({ label, children }) {
  return (
    <div>
      <h2 className="text-sm font-medium text-muted">{label}</h2>
      <div className="mt-1 text-ink">{children}</div>
    </div>
  )
}

function ApplicationDetailPage() {
  const { applicationId } = useParams()
  const navigate = useNavigate()
  const [application, setApplication] = useState(null)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  const loadApplication = useCallback(async () => {
    setStatus('loading')
    setError('')
    try {
      const data = await getApplication(applicationId)
      setApplication(data)
      setStatus('ready')
    } catch (err) {
      setError(
        err.response?.status === 404
          ? 'Application not found.'
          : getApiErrorMessage(err, 'Unable to load the application.'),
      )
      setStatus('error')
    }
  }, [applicationId])

  useEffect(() => {
    loadApplication()
  }, [loadApplication])

  async function handleConfirmDelete() {
    setIsDeleting(true)
    setDeleteError('')
    try {
      await deleteApplication(applicationId)
      navigate('/applications', { replace: true })
    } catch (err) {
      setDeleteError(getApiErrorMessage(err, 'Unable to delete the application.'))
      setShowDeleteConfirm(false)
      setIsDeleting(false)
    }
  }

  return (
    <Page>
      <p className="text-sm">
        <Link
          className="underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          to="/applications"
        >
          Back to applications
        </Link>
      </p>

      {status === 'loading' ? (
        <div className="mt-8">
          <LoadingState message="Loading application…" />
        </div>
      ) : null}

      {status === 'error' ? (
        <div className="mt-8">
          <ErrorState message={error} onRetry={loadApplication} />
        </div>
      ) : null}

      {status === 'ready' && application ? (
        <div className="mt-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="font-display text-3xl font-semibold tracking-tight text-ink">
                {application.company_name}
              </h1>
              <p className="mt-2 text-lg text-muted">{application.role_title}</p>
              <div className="mt-3">
                <StatusBadge status={application.status} />
              </div>
            </div>
            <div className="flex gap-2">
              <Link className={buttonClass('secondary')} to={`/applications/${application.id}/edit`}>
                Edit
              </Link>
              <button
                className={buttonClass('danger')}
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
              >
                Delete
              </button>
            </div>
          </div>

          {deleteError ? <Alert className="mt-4">{deleteError}</Alert> : null}

          <div className="mt-8 grid gap-6 rounded-lg border border-line bg-surface p-4 sm:p-6 md:grid-cols-2">
            <DetailField label="Deadline">{formatDate(application.deadline)}</DetailField>
            <DetailField label="Applied date">{formatDate(application.applied_date)}</DetailField>
            <DetailField label="Resume version">{application.resume_version || '—'}</DetailField>
            <DetailField label="Updated">{formatDateTime(application.updated_at)}</DetailField>
          </div>

          <div className="mt-8 rounded-lg border border-line bg-surface p-4 sm:p-6">
            <DetailField label="Notes">
              <p className="whitespace-pre-wrap">{application.notes || '—'}</p>
            </DetailField>
          </div>

          <div className="mt-8 rounded-lg border border-line bg-surface p-4 sm:p-6">
            <DetailField label="Job description">
              <p className="whitespace-pre-wrap">{application.job_description || '—'}</p>
            </DetailField>
          </div>

          <InterviewSection applicationId={applicationId} />
        </div>
      ) : null}

      {showDeleteConfirm ? (
        <ConfirmDialog
          title="Delete this application?"
          message="This application and its interview rounds will be deleted. This cannot be undone."
          confirmLabel="Delete application"
          isConfirming={isDeleting}
          onCancel={() => setShowDeleteConfirm(false)}
          onConfirm={handleConfirmDelete}
        />
      ) : null}
    </Page>
  )
}

export default ApplicationDetailPage

import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import ApplicationForm from '../components/ApplicationForm'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import { getApplication, updateApplication } from '../services/applications'
import { getApiErrorMessage } from '../services/authErrors'
import {
  applicationFormFromRecord,
  changedApplicationFields,
  validateApplicationForm,
} from '../utils/applicationPayload'

function ApplicationEditPage() {
  const { applicationId } = useParams()
  const navigate = useNavigate()
  const [application, setApplication] = useState(null)
  const [values, setValues] = useState(null)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')
  const [formError, setFormError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    let cancelled = false
    setStatus('loading')
    setError('')
    getApplication(applicationId)
      .then((data) => {
        if (cancelled) {
          return
        }
        setApplication(data)
        setValues(applicationFormFromRecord(data))
        setStatus('ready')
      })
      .catch((err) => {
        if (cancelled) {
          return
        }
        setError(
          err.response?.status === 404
            ? 'Application not found.'
            : getApiErrorMessage(err, 'Unable to load the application.'),
        )
        setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [applicationId])

  async function handleSubmit(event) {
    event.preventDefault()
    const validationError = validateApplicationForm(values)
    if (validationError) {
      setFormError(validationError)
      return
    }

    const patch = changedApplicationFields(application, values)
    if (Object.keys(patch).length === 0) {
      navigate(`/applications/${applicationId}`)
      return
    }

    setFormError('')
    setIsSubmitting(true)
    try {
      await updateApplication(applicationId, patch)
      navigate(`/applications/${applicationId}`)
    } catch (err) {
      setFormError(getApiErrorMessage(err, 'Unable to update the application.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-10">
      <p className="text-sm">
        <Link className="underline" to={`/applications/${applicationId}`}>
          Back to application
        </Link>
      </p>
      <h1 className="mt-4 text-3xl font-semibold text-neutral-900">Edit application</h1>

      {status === 'loading' ? (
        <div className="mt-8">
          <LoadingState message="Loading application…" />
        </div>
      ) : null}

      {status === 'error' ? (
        <div className="mt-8">
          <ErrorState message={error} />
        </div>
      ) : null}

      {status === 'ready' && values ? (
        <div className="mt-8">
          <ApplicationForm
            values={values}
            onChange={setValues}
            onSubmit={handleSubmit}
            submitLabel="Save changes"
            isSubmitting={isSubmitting}
            error={formError}
          />
        </div>
      ) : null}
    </main>
  )
}

export default ApplicationEditPage

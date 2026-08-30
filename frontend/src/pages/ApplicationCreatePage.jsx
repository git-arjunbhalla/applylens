import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import ApplicationForm from '../components/ApplicationForm'
import { createApplication } from '../services/applications'
import { getApiErrorMessage } from '../services/authErrors'
import { normalizeApplicationForm, validateApplicationForm } from '../utils/applicationPayload'

const emptyForm = {
  company_name: '',
  role_title: '',
  status: 'Wishlist',
  applied_date: '',
  deadline: '',
  notes: '',
  job_description: '',
  resume_version: '',
}

function ApplicationCreatePage() {
  const navigate = useNavigate()
  const [values, setValues] = useState(emptyForm)
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    const validationError = validateApplicationForm(values)
    if (validationError) {
      setError(validationError)
      return
    }

    setError('')
    setIsSubmitting(true)
    try {
      const created = await createApplication(normalizeApplicationForm(values))
      navigate(`/applications/${created.id}`, { replace: true })
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to create the application.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-10">
      <p className="text-sm">
        <Link className="underline" to="/applications">
          Back to applications
        </Link>
      </p>
      <h1 className="mt-4 text-3xl font-semibold text-neutral-900">New application</h1>
      <div className="mt-8">
        <ApplicationForm
          values={values}
          onChange={setValues}
          onSubmit={handleSubmit}
          submitLabel="Create application"
          isSubmitting={isSubmitting}
          error={error}
        />
      </div>
    </main>
  )
}

export default ApplicationCreatePage

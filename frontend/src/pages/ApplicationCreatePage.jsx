import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import ApplicationForm from '../components/ApplicationForm'
import Page from '../components/Page'
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
    <Page width="narrow">
      <p className="text-sm">
        <Link
          className="underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          to="/applications"
        >
          Back to applications
        </Link>
      </p>
      <h1 className="mt-4 font-display text-3xl font-semibold tracking-tight text-ink">New application</h1>
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
    </Page>
  )
}

export default ApplicationCreatePage

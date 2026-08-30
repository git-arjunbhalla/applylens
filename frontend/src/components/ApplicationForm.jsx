import { APPLICATION_STATUSES } from '../constants/applications'
import Alert from './Alert'
import Button from './Button'
import Field, { inputClass } from './Field'

function ApplicationForm({ values, onChange, onSubmit, submitLabel, isSubmitting, error }) {
  function handleChange(event) {
    const { name, value } = event.target
    onChange({ ...values, [name]: value })
  }

  return (
    <form className="space-y-4" onSubmit={onSubmit} noValidate>
      {error ? <Alert>{error}</Alert> : null}

      <Field label="Company">
        <input className={inputClass} name="company_name" value={values.company_name} onChange={handleChange} />
      </Field>

      <Field label="Role">
        <input className={inputClass} name="role_title" value={values.role_title} onChange={handleChange} />
      </Field>

      <Field label="Status">
        <select className={inputClass} name="status" value={values.status} onChange={handleChange}>
          {APPLICATION_STATUSES.map((status) => (
            <option key={status} value={status}>
              {status}
            </option>
          ))}
        </select>
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Applied date">
          <input
            className={inputClass}
            type="date"
            name="applied_date"
            value={values.applied_date}
            onChange={handleChange}
          />
        </Field>

        <Field label="Deadline">
          <input
            className={inputClass}
            type="date"
            name="deadline"
            value={values.deadline}
            onChange={handleChange}
          />
        </Field>
      </div>

      <Field label="Resume version">
        <input className={inputClass} name="resume_version" value={values.resume_version} onChange={handleChange} />
      </Field>

      <Field label="Notes">
        <textarea className={inputClass} name="notes" rows={4} value={values.notes} onChange={handleChange} />
      </Field>

      <Field label="Job description">
        <textarea
          className={inputClass}
          name="job_description"
          rows={8}
          value={values.job_description}
          onChange={handleChange}
        />
      </Field>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Saving…' : submitLabel}
      </Button>
    </form>
  )
}

export default ApplicationForm

import { APPLICATION_STATUSES } from '../constants/applications'

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="text-sm text-neutral-700">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  )
}

const inputClass = 'w-full rounded border border-neutral-300 px-3 py-2'

function ApplicationForm({ values, onChange, onSubmit, submitLabel, isSubmitting, error }) {
  function handleChange(event) {
    const { name, value } = event.target
    onChange({ ...values, [name]: value })
  }

  return (
    <form className="space-y-4" onSubmit={onSubmit} noValidate>
      {error ? (
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800" role="alert">
          {error}
        </p>
      ) : null}

      <Field label="Company">
        <input
          className={inputClass}
          name="company_name"
          value={values.company_name}
          onChange={handleChange}
        />
      </Field>

      <Field label="Role">
        <input
          className={inputClass}
          name="role_title"
          value={values.role_title}
          onChange={handleChange}
        />
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

      <Field label="Resume version">
        <input
          className={inputClass}
          name="resume_version"
          value={values.resume_version}
          onChange={handleChange}
        />
      </Field>

      <Field label="Notes">
        <textarea
          className={inputClass}
          name="notes"
          rows={4}
          value={values.notes}
          onChange={handleChange}
        />
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

      <button
        className="rounded bg-neutral-900 px-3 py-2 text-white disabled:opacity-60"
        type="submit"
        disabled={isSubmitting}
      >
        {isSubmitting ? 'Saving…' : submitLabel}
      </button>
    </form>
  )
}

export default ApplicationForm

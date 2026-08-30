import { useCallback, useEffect, useState } from 'react'
import { INTERVIEW_OUTCOMES } from '../constants/interviews'
import { getApiErrorMessage } from '../services/authErrors'
import {
  createInterview,
  deleteInterview,
  listInterviews,
  updateInterview,
} from '../services/interviews'
import { formatDateTime, localDateTimeToIso, toDateTimeLocalValue } from '../utils/dates'
import Alert from './Alert'
import Button from './Button'
import ConfirmDialog from './ConfirmDialog'
import EmptyState from './EmptyState'
import ErrorState from './ErrorState'
import { inputClass } from './Field'
import LoadingState from './LoadingState'

const emptyForm = {
  round_name: '',
  scheduled_at: '',
  notes: '',
  outcome: 'Pending',
}

function interviewToForm(interview) {
  return {
    round_name: interview.round_name ?? '',
    scheduled_at: toDateTimeLocalValue(interview.scheduled_at),
    notes: interview.notes ?? '',
    outcome: interview.outcome ?? 'Pending',
  }
}

function buildInterviewPayload(values, { includeEmptySchedule = false } = {}) {
  const payload = {
    round_name: values.round_name.trim(),
    notes: values.notes.trim() ? values.notes.trim() : null,
    outcome: values.outcome,
  }
  if (values.scheduled_at) {
    payload.scheduled_at = localDateTimeToIso(values.scheduled_at)
  } else if (includeEmptySchedule) {
    payload.scheduled_at = null
  }
  return payload
}

function changedInterviewFields(original, values) {
  const next = buildInterviewPayload(values, { includeEmptySchedule: true })
  const originalScheduled = original.scheduled_at
    ? new Date(original.scheduled_at).toISOString()
    : null
  const patch = {}

  if (original.round_name !== next.round_name) {
    patch.round_name = next.round_name
  }
  if ((original.notes ?? null) !== next.notes) {
    patch.notes = next.notes
  }
  if (original.outcome !== next.outcome) {
    patch.outcome = next.outcome
  }
  if (originalScheduled !== next.scheduled_at) {
    patch.scheduled_at = next.scheduled_at
  }

  return patch
}

function validateInterviewForm(values) {
  if (!values.round_name.trim()) {
    return 'Round name is required.'
  }
  if (values.round_name.trim().length > 255) {
    return 'Round name must be at most 255 characters.'
  }
  if (values.scheduled_at) {
    const iso = localDateTimeToIso(values.scheduled_at)
    if (!iso) {
      return 'Enter a valid scheduled time.'
    }
  }
  return null
}

function InterviewFormFields({ values, onChange }) {
  function handleChange(event) {
    const { name, value } = event.target
    onChange({ ...values, [name]: value })
  }

  return (
    <div className="space-y-3">
      <label className="block">
        <span className="text-sm text-muted">Round name</span>
        <input
          className={`${inputClass} mt-1`}
          name="round_name"
          value={values.round_name}
          onChange={handleChange}
        />
      </label>
      <label className="block">
        <span className="text-sm text-muted">Scheduled time</span>
        <input
          className={`${inputClass} mt-1`}
          type="datetime-local"
          name="scheduled_at"
          value={values.scheduled_at}
          onChange={handleChange}
        />
      </label>
      <label className="block">
        <span className="text-sm text-muted">Outcome</span>
        <select
          className={`${inputClass} mt-1`}
          name="outcome"
          value={values.outcome}
          onChange={handleChange}
        >
          {INTERVIEW_OUTCOMES.map((outcome) => (
            <option key={outcome} value={outcome}>
              {outcome}
            </option>
          ))}
        </select>
      </label>
      <label className="block">
        <span className="text-sm text-muted">Notes</span>
        <textarea
          className={`${inputClass} mt-1`}
          name="notes"
          rows={3}
          value={values.notes}
          onChange={handleChange}
        />
      </label>
    </div>
  )
}

function InterviewSection({ applicationId }) {
  const [interviews, setInterviews] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')
  const [formError, setFormError] = useState('')
  const [isCreating, setIsCreating] = useState(false)
  const [createValues, setCreateValues] = useState(emptyForm)
  const [isSavingCreate, setIsSavingCreate] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [editValues, setEditValues] = useState(emptyForm)
  const [isSavingEdit, setIsSavingEdit] = useState(false)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const loadInterviews = useCallback(async () => {
    setStatus('loading')
    setError('')
    try {
      const data = await listInterviews(applicationId)
      setInterviews(data)
      setStatus('ready')
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load interview rounds.'))
      setStatus('error')
    }
  }, [applicationId])

  useEffect(() => {
    loadInterviews()
  }, [loadInterviews])

  async function handleCreate(event) {
    event.preventDefault()
    const validationError = validateInterviewForm(createValues)
    if (validationError) {
      setFormError(validationError)
      return
    }

    setFormError('')
    setIsSavingCreate(true)
    try {
      const created = await createInterview(applicationId, buildInterviewPayload(createValues))
      setInterviews((current) => [...current, created])
      setCreateValues(emptyForm)
      setIsCreating(false)
    } catch (err) {
      setFormError(getApiErrorMessage(err, 'Unable to create the interview round.'))
    } finally {
      setIsSavingCreate(false)
    }
  }

  async function handleEdit(event) {
    event.preventDefault()
    const original = interviews.find((item) => item.id === editingId)
    if (!original) {
      return
    }

    const validationError = validateInterviewForm(editValues)
    if (validationError) {
      setFormError(validationError)
      return
    }

    const patch = changedInterviewFields(original, editValues)
    if (Object.keys(patch).length === 0) {
      setEditingId(null)
      setFormError('')
      return
    }

    setFormError('')
    setIsSavingEdit(true)
    try {
      const updated = await updateInterview(applicationId, editingId, patch)
      setInterviews((current) => current.map((item) => (item.id === updated.id ? updated : item)))
      setEditingId(null)
    } catch (err) {
      setFormError(getApiErrorMessage(err, 'Unable to update the interview round.'))
    } finally {
      setIsSavingEdit(false)
    }
  }

  async function handleConfirmDelete() {
    if (!pendingDelete) {
      return
    }
    setIsDeleting(true)
    setFormError('')
    try {
      await deleteInterview(applicationId, pendingDelete.id)
      setInterviews((current) => current.filter((item) => item.id !== pendingDelete.id))
      if (editingId === pendingDelete.id) {
        setEditingId(null)
      }
      setPendingDelete(null)
    } catch (err) {
      setFormError(getApiErrorMessage(err, 'Unable to delete the interview round.'))
      setPendingDelete(null)
    } finally {
      setIsDeleting(false)
    }
  }

  if (status === 'loading') {
    return (
      <section className="mt-10">
        <h2 className="font-display text-xl font-semibold text-ink">Interview rounds</h2>
        <div className="mt-4">
          <LoadingState message="Loading interview rounds…" />
        </div>
      </section>
    )
  }

  if (status === 'error') {
    return (
      <section className="mt-10">
        <h2 className="font-display text-xl font-semibold text-ink">Interview rounds</h2>
        <div className="mt-4">
          <ErrorState message={error} onRetry={loadInterviews} />
        </div>
      </section>
    )
  }

  return (
    <section className="mt-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-display text-xl font-semibold text-ink">Interview rounds</h2>
        {!isCreating ? (
          <Button
            variant="secondary"
            type="button"
            onClick={() => {
              setIsCreating(true)
              setFormError('')
              setCreateValues(emptyForm)
            }}
          >
            Add interview round
          </Button>
        ) : null}
      </div>

      {formError ? <Alert className="mt-4">{formError}</Alert> : null}

      {isCreating ? (
        <form className="mt-4 rounded-lg border border-line bg-surface p-4" onSubmit={handleCreate} noValidate>
          <h3 className="font-medium text-ink">New interview round</h3>
          <div className="mt-3">
            <InterviewFormFields values={createValues} onChange={setCreateValues} />
          </div>
          <div className="mt-4 flex gap-3">
            <Button type="submit" disabled={isSavingCreate}>
              {isSavingCreate ? 'Saving…' : 'Create round'}
            </Button>
            <Button
              variant="secondary"
              type="button"
              onClick={() => {
                setIsCreating(false)
                setFormError('')
              }}
            >
              Cancel
            </Button>
          </div>
        </form>
      ) : null}

      {interviews.length === 0 && !isCreating ? (
        <div className="mt-4">
          <EmptyState
            title="No interview rounds yet"
            message="Add a round to track scheduled interviews and outcomes."
          />
        </div>
      ) : (
        <ul className="mt-4 space-y-3">
          {interviews.map((interview) => (
            <li key={interview.id} className="rounded-lg border border-line bg-surface p-4">
              {editingId === interview.id ? (
                <form onSubmit={handleEdit} noValidate>
                  <InterviewFormFields values={editValues} onChange={setEditValues} />
                  <div className="mt-4 flex gap-3">
                    <Button type="submit" disabled={isSavingEdit}>
                      {isSavingEdit ? 'Saving…' : 'Save round'}
                    </Button>
                    <Button
                      variant="secondary"
                      type="button"
                      onClick={() => {
                        setEditingId(null)
                        setFormError('')
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </form>
              ) : (
                <div>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-ink">{interview.round_name}</p>
                      <p className="mt-1 text-sm text-muted">{formatDateTime(interview.scheduled_at)}</p>
                      <p className="mt-1 text-sm text-ink">Outcome: {interview.outcome}</p>
                      {interview.notes ? (
                        <p className="mt-2 whitespace-pre-wrap text-sm text-muted">{interview.notes}</p>
                      ) : null}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="secondary"
                        type="button"
                        onClick={() => {
                          setEditingId(interview.id)
                          setEditValues(interviewToForm(interview))
                          setFormError('')
                        }}
                      >
                        Edit
                      </Button>
                      <Button variant="danger" type="button" onClick={() => setPendingDelete(interview)}>
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}

      {pendingDelete ? (
        <ConfirmDialog
          title="Delete interview round?"
          message={`This will delete the “${pendingDelete.round_name}” interview round. This cannot be undone.`}
          confirmLabel="Delete round"
          isConfirming={isDeleting}
          onCancel={() => setPendingDelete(null)}
          onConfirm={handleConfirmDelete}
        />
      ) : null}
    </section>
  )
}

export default InterviewSection

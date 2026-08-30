import { APPLICATION_FORM_FIELDS } from '../constants/applications'

function emptyToNull(value) {
  if (value == null) {
    return null
  }
  if (typeof value === 'string') {
    const trimmed = value.trim()
    return trimmed === '' ? null : trimmed
  }
  return value
}

export function normalizeApplicationForm(values) {
  return {
    company_name: values.company_name.trim(),
    role_title: values.role_title.trim(),
    status: values.status,
    applied_date: emptyToNull(values.applied_date),
    deadline: emptyToNull(values.deadline),
    notes: emptyToNull(values.notes),
    job_description: emptyToNull(values.job_description),
    resume_version: emptyToNull(values.resume_version),
  }
}

export function validateApplicationForm(values) {
  if (!values.company_name.trim()) {
    return 'Company is required.'
  }
  if (values.company_name.trim().length > 255) {
    return 'Company must be at most 255 characters.'
  }
  if (!values.role_title.trim()) {
    return 'Role is required.'
  }
  if (values.role_title.trim().length > 255) {
    return 'Role must be at most 255 characters.'
  }
  if (values.resume_version.trim().length > 255) {
    return 'Resume version must be at most 255 characters.'
  }
  return null
}

export function applicationFormFromRecord(application) {
  return {
    company_name: application.company_name ?? '',
    role_title: application.role_title ?? '',
    status: application.status ?? 'Wishlist',
    applied_date: application.applied_date ?? '',
    deadline: application.deadline ?? '',
    notes: application.notes ?? '',
    job_description: application.job_description ?? '',
    resume_version: application.resume_version ?? '',
  }
}

export function changedApplicationFields(original, next) {
  const originalNormalized = normalizeApplicationForm(applicationFormFromRecord(original))
  const nextNormalized = normalizeApplicationForm(next)
  const patch = {}

  for (const field of APPLICATION_FORM_FIELDS) {
    if (originalNormalized[field] !== nextNormalized[field]) {
      patch[field] = nextNormalized[field]
    }
  }

  return patch
}

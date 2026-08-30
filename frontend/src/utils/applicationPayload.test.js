import { describe, expect, it } from 'vitest'
import {
  applicationFormFromRecord,
  changedApplicationFields,
  normalizeApplicationForm,
  validateApplicationForm,
} from './applicationPayload'

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

describe('application payload helpers', () => {
  it('requires company and role', () => {
    expect(validateApplicationForm(emptyForm)).toBe('Company is required.')
    expect(
      validateApplicationForm({ ...emptyForm, company_name: 'Acme' }),
    ).toBe('Role is required.')
    expect(
      validateApplicationForm({ ...emptyForm, company_name: 'Acme', role_title: 'Engineer' }),
    ).toBeNull()
  })

  it('sends only changed fields for partial updates', () => {
    const original = {
      company_name: 'Acme',
      role_title: 'Engineer',
      status: 'Applied',
      applied_date: '2026-01-15',
      deadline: '2026-02-01',
      notes: 'Follow up',
      job_description: 'Build things',
      resume_version: 'v1',
    }
    const next = applicationFormFromRecord(original)
    next.notes = 'Updated notes'
    next.status = 'Interviewing'

    expect(changedApplicationFields(original, next)).toEqual({
      notes: 'Updated notes',
      status: 'Interviewing',
    })
  })

  it('normalizes blank optional fields to null', () => {
    expect(
      normalizeApplicationForm({
        ...emptyForm,
        company_name: '  Acme  ',
        role_title: 'Engineer',
        notes: '   ',
      }),
    ).toMatchObject({
      company_name: 'Acme',
      notes: null,
    })
  })
})

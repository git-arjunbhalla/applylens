export const APPLICATION_STATUSES = [
  'Wishlist',
  'Applied',
  'OA',
  'Interviewing',
  'Offer',
  'Rejected',
]

export const APPLICATION_SORT_FIELDS = [
  { value: 'created_at', label: 'Created' },
  { value: 'updated_at', label: 'Updated' },
  { value: 'deadline', label: 'Deadline' },
  { value: 'applied_date', label: 'Applied date' },
  { value: 'company_name', label: 'Company' },
  { value: 'role_title', label: 'Role' },
  { value: 'status', label: 'Status' },
]

export const PAGE_SIZE_OPTIONS = [10, 20, 50]

export const APPLICATION_FORM_FIELDS = [
  'company_name',
  'role_title',
  'status',
  'applied_date',
  'deadline',
  'notes',
  'job_description',
  'resume_version',
]

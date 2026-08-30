import api from './api'

export async function listApplications(filters = {}, config = {}) {
  const params = {
    page: filters.page ?? 1,
    page_size: filters.page_size ?? 20,
    sort: filters.sort ?? 'created_at',
    order: filters.order ?? 'desc',
  }

  if (filters.status) {
    params.status = filters.status
  }
  if (filters.company?.trim()) {
    params.company = filters.company.trim()
  }
  if (filters.deadline_before) {
    params.deadline_before = filters.deadline_before
  }
  if (filters.deadline_after) {
    params.deadline_after = filters.deadline_after
  }
  if (filters.search?.trim()) {
    params.search = filters.search.trim()
  }

  const { data } = await api.get('/api/v1/applications', { ...config, params })
  return data
}

export async function getApplication(applicationId, config = {}) {
  const { data } = await api.get(`/api/v1/applications/${applicationId}`, config)
  return data
}

export async function createApplication(payload, config = {}) {
  const { data } = await api.post('/api/v1/applications', payload, config)
  return data
}

export async function updateApplication(applicationId, payload, config = {}) {
  const { data } = await api.put(`/api/v1/applications/${applicationId}`, payload, config)
  return data
}

export async function deleteApplication(applicationId, config = {}) {
  await api.delete(`/api/v1/applications/${applicationId}`, config)
}

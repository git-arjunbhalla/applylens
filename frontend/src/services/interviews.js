import api from './api'

export async function listInterviews(applicationId, config = {}) {
  const { data } = await api.get(`/api/v1/applications/${applicationId}/interviews`, config)
  return data
}

export async function createInterview(applicationId, payload, config = {}) {
  const { data } = await api.post(
    `/api/v1/applications/${applicationId}/interviews`,
    payload,
    config,
  )
  return data
}

export async function updateInterview(applicationId, interviewId, payload, config = {}) {
  const { data } = await api.put(
    `/api/v1/applications/${applicationId}/interviews/${interviewId}`,
    payload,
    config,
  )
  return data
}

export async function deleteInterview(applicationId, interviewId, config = {}) {
  await api.delete(`/api/v1/applications/${applicationId}/interviews/${interviewId}`, config)
}

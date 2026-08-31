import api from './api'

export async function analyzeResume(payload, config = {}) {
  const { data } = await api.post(
    '/api/v1/ai/resume-analysis',
    {
      resume_text: payload.resume_text,
      job_description: payload.job_description,
    },
    config,
  )
  return data
}

export async function matchJobDescription(payload, config = {}) {
  const { data } = await api.post(
    '/api/v1/ai/jd-match',
    {
      resume_text: payload.resume_text,
      job_description: payload.job_description,
    },
    config,
  )
  return data
}

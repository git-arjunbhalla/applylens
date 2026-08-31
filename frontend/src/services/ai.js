import api from './api'

export const RESUME_PDF_MAX_BYTES = 5 * 1024 * 1024

export async function analyzeResume(payload, config = {}) {
  const formData = new FormData()
  formData.append('resume', payload.resume)
  const { data } = await api.post('/api/v1/ai/resume-analysis', formData, {
    ...config,
    headers: {
      ...config.headers,
      'Content-Type': undefined,
    },
  })
  return data
}

export async function matchJobDescription(payload, config = {}) {
  const formData = new FormData()
  formData.append('resume', payload.resume)
  formData.append('job_description', payload.job_description)
  const { data } = await api.post('/api/v1/ai/jd-match', formData, {
    ...config,
    headers: {
      ...config.headers,
      'Content-Type': undefined,
    },
  })
  return data
}

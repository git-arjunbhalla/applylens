import api from './api'

export async function getAnalyticsSummary(config = {}) {
  const { data } = await api.get('/api/v1/analytics/summary', config)
  return data
}

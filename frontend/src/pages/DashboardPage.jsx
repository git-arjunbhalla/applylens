import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { APPLICATION_STATUSES } from '../constants/applications'
import { getAnalyticsSummary } from '../services/analytics'
import { listApplications } from '../services/applications'
import { getApiErrorMessage } from '../services/authErrors'
import { formatDate, formatResponseRate } from '../utils/dates'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import StatusBadge from '../components/StatusBadge'

function Metric({ label, value }) {
  return (
    <div className="rounded border border-neutral-200 p-4">
      <p className="text-sm text-neutral-600">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-neutral-900">{value}</p>
    </div>
  )
}

function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [recent, setRecent] = useState([])
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')
  const [recentError, setRecentError] = useState('')

  const loadDashboard = useCallback(async () => {
    setStatus('loading')
    setError('')
    setRecentError('')
    try {
      const analytics = await getAnalyticsSummary()
      setSummary(analytics)
      setStatus('ready')
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to load analytics.'))
      setStatus('error')
      return
    }

    try {
      const list = await listApplications({
        page: 1,
        page_size: 5,
        sort: 'updated_at',
        order: 'desc',
      })
      setRecent(list.items)
    } catch (err) {
      setRecentError(getApiErrorMessage(err, 'Unable to load recent applications.'))
      setRecent([])
    }
  }, [])

  useEffect(() => {
    loadDashboard()
  }, [loadDashboard])

  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-neutral-900">Dashboard</h1>
          <p className="mt-2 text-neutral-600">Overview of your applications.</p>
        </div>
        <Link className="rounded bg-neutral-900 px-3 py-2 text-white" to="/applications/new">
          New application
        </Link>
      </div>

      {status === 'loading' ? (
        <div className="mt-8">
          <LoadingState message="Loading analytics…" />
        </div>
      ) : null}

      {status === 'error' ? (
        <div className="mt-8">
          <ErrorState message={error} onRetry={loadDashboard} />
        </div>
      ) : null}

      {status === 'ready' && summary ? (
        <div className="mt-8 space-y-8">
          {summary.total_applications === 0 ? (
            <EmptyState
              title="No applications yet"
              message="Create an application to start tracking jobs and internships."
              action={
                <Link className="rounded bg-neutral-900 px-3 py-2 text-white" to="/applications/new">
                  Create application
                </Link>
              }
            />
          ) : null}

          <section>
            <h2 className="text-lg font-medium text-neutral-900">Summary</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Metric label="Total applications" value={summary.total_applications} />
              <Metric label="Upcoming deadlines" value={summary.upcoming_deadlines} />
              <Metric label="Interview count" value={summary.interview_count} />
              <Metric label="Offers" value={summary.offers} />
              <Metric label="Rejections" value={summary.rejections} />
              <Metric label="Response rate" value={formatResponseRate(summary.response_rate)} />
              <Metric
                label="Average time to response"
                value={
                  summary.average_time_to_response_days == null
                    ? 'Not available'
                    : `${summary.average_time_to_response_days} days`
                }
              />
            </div>
          </section>

          <section>
            <h2 className="text-lg font-medium text-neutral-900">Status breakdown</h2>
            <ul className="mt-4 divide-y divide-neutral-200 rounded border border-neutral-200">
              {APPLICATION_STATUSES.map((statusName) => (
                <li key={statusName} className="flex items-center justify-between px-4 py-3">
                  <StatusBadge status={statusName} />
                  <span>{summary.counts_by_status[statusName] ?? 0}</span>
                </li>
              ))}
            </ul>
          </section>

          <section>
            <h2 className="text-lg font-medium text-neutral-900">Recent activity</h2>
            {recentError ? (
              <div className="mt-4">
                <ErrorState message={recentError} onRetry={loadDashboard} />
              </div>
            ) : recent.length === 0 ? (
              <p className="mt-4 text-neutral-600">No recent application activity.</p>
            ) : (
              <ul className="mt-4 divide-y divide-neutral-200 rounded border border-neutral-200">
                {recent.map((application) => (
                  <li key={application.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
                    <div>
                      <Link className="font-medium underline" to={`/applications/${application.id}`}>
                        {application.company_name}
                      </Link>
                      <p className="text-sm text-neutral-600">{application.role_title}</p>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <StatusBadge status={application.status} />
                      <span className="text-neutral-600">Deadline {formatDate(application.deadline)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      ) : null}
    </main>
  )
}

export default DashboardPage

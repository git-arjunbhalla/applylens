import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { APPLICATION_STATUSES } from '../constants/applications'
import { getAnalyticsSummary } from '../services/analytics'
import { listApplications } from '../services/applications'
import { getApiErrorMessage } from '../services/authErrors'
import { formatDate, formatResponseRate } from '../utils/dates'
import { buttonClass } from '../components/Button'
import Card from '../components/Card'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import LoadingState from '../components/LoadingState'
import Page, { PageHeader } from '../components/Page'
import StatusBadge from '../components/StatusBadge'
import StatusBreakdownChart from '../components/StatusBreakdownChart'

function Metric({ label, value, emphasis = false }) {
  return (
    <Card className={`p-4 ${emphasis ? 'bg-linear-to-br from-[var(--al-hero-from)] to-[var(--al-hero-to)]' : ''}`}>
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-2 font-display text-2xl font-semibold text-ink">{value}</p>
    </Card>
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

  const chartData = useMemo(
    () =>
      APPLICATION_STATUSES.map((statusName) => ({
        status: statusName,
        count: summary?.counts_by_status?.[statusName] ?? 0,
      })),
    [summary],
  )

  return (
    <Page>
      <PageHeader
        title="Dashboard"
        description="Overview of your applications."
        action={
          <Link className={buttonClass('primary')} to="/applications/new">
            New application
          </Link>
        }
      />

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
                <Link className={buttonClass('primary')} to="/applications/new">
                  Create application
                </Link>
              }
            />
          ) : null}

          <section>
            <h2 className="font-display text-lg font-medium text-ink">Summary</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <Metric label="Total applications" value={summary.total_applications} emphasis />
              <Metric label="Upcoming deadlines" value={summary.upcoming_deadlines} />
              <Metric label="Interview count" value={summary.interview_count} />
              <Metric label="Offers" value={summary.offers} />
              <Metric label="Rejections" value={summary.rejections} />
              <Metric label="Response rate" value={formatResponseRate(summary.response_rate)} />
            </div>
            <p className="mt-4 text-sm text-muted">
              Average time to response:{' '}
              <span className="text-ink">
                {summary.average_time_to_response_days == null
                  ? 'Not available'
                  : `${summary.average_time_to_response_days} days`}
              </span>
            </p>
          </section>

          <section>
            <h2 className="font-display text-lg font-medium text-ink">Status breakdown</h2>
            <div className="mt-4 grid gap-4 lg:grid-cols-2">
              {summary.total_applications > 0 ? (
                <Card className="p-3 sm:p-4">
                  <StatusBreakdownChart data={chartData} />
                </Card>
              ) : null}
              <ul className="divide-y divide-line rounded-lg border border-line bg-surface">
                {APPLICATION_STATUSES.map((statusName) => (
                  <li key={statusName} className="flex items-center justify-between px-4 py-3">
                    <StatusBadge status={statusName} />
                    <span>{summary.counts_by_status[statusName] ?? 0}</span>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <section>
            <h2 className="font-display text-lg font-medium text-ink">Recent activity</h2>
            {recentError ? (
              <div className="mt-4">
                <ErrorState message={recentError} onRetry={loadDashboard} />
              </div>
            ) : recent.length === 0 ? (
              <p className="mt-4 text-muted">No recent application activity.</p>
            ) : (
              <ul className="mt-4 divide-y divide-line rounded-lg border border-line bg-surface">
                {recent.map((application) => (
                  <li key={application.id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-3">
                    <div>
                      <Link
                        className="font-medium underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                        to={`/applications/${application.id}`}
                      >
                        {application.company_name}
                      </Link>
                      <p className="text-sm text-muted">{application.role_title}</p>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <StatusBadge status={application.status} />
                      <span className="text-muted">Deadline {formatDate(application.deadline)}</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      ) : null}
    </Page>
  )
}

export default DashboardPage

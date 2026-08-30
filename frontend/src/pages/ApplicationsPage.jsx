import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import Button, { buttonClass } from '../components/Button'
import EmptyState from '../components/EmptyState'
import ErrorState from '../components/ErrorState'
import { inputClass } from '../components/Field'
import LoadingState from '../components/LoadingState'
import Page, { PageHeader } from '../components/Page'
import StatusBadge from '../components/StatusBadge'
import {
  APPLICATION_SORT_FIELDS,
  APPLICATION_STATUSES,
  PAGE_SIZE_OPTIONS,
} from '../constants/applications'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { listApplications } from '../services/applications'
import { getApiErrorMessage } from '../services/authErrors'
import { formatDate } from '../utils/dates'

function ApplicationsPage() {
  const [searchInput, setSearchInput] = useState('')
  const [companyInput, setCompanyInput] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [deadlineAfter, setDeadlineAfter] = useState('')
  const [deadlineBefore, setDeadlineBefore] = useState('')
  const [sort, setSort] = useState('created_at')
  const [order, setOrder] = useState('desc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [status, setStatus] = useState('loading')
  const [error, setError] = useState('')
  const [reloadNonce, setReloadNonce] = useState(0)

  const search = useDebouncedValue(searchInput)
  const company = useDebouncedValue(companyInput)

  const filters = useMemo(
    () => ({
      page,
      page_size: pageSize,
      sort,
      order,
      status: statusFilter || undefined,
      company: company || undefined,
      deadline_after: deadlineAfter || undefined,
      deadline_before: deadlineBefore || undefined,
      search: search || undefined,
    }),
    [page, pageSize, sort, order, statusFilter, company, deadlineAfter, deadlineBefore, search],
  )

  const hasActiveFilters = Boolean(
    searchInput || companyInput || statusFilter || deadlineAfter || deadlineBefore,
  )

  useEffect(() => {
    const controller = new AbortController()
    setStatus('loading')
    setError('')

    listApplications(filters, { signal: controller.signal })
      .then((data) => {
        setItems(data.items)
        setTotal(data.total)
        setStatus('ready')
      })
      .catch((err) => {
        if (err.code === 'ERR_CANCELED' || err.name === 'CanceledError') {
          return
        }
        setError(getApiErrorMessage(err, 'Unable to load applications.'))
        setStatus('error')
      })

    return () => controller.abort()
  }, [filters, reloadNonce])

  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const canPrevious = page > 1
  const canNext = page * pageSize < total

  function clearFilters() {
    setSearchInput('')
    setCompanyInput('')
    setStatusFilter('')
    setDeadlineAfter('')
    setDeadlineBefore('')
    setSort('created_at')
    setOrder('desc')
    setPage(1)
  }

  return (
    <Page>
      <PageHeader
        title="Applications"
        description="Search, filter, and track your applications."
        action={
          <Link className={buttonClass('primary')} to="/applications/new">
            New application
          </Link>
        }
      />

      <form
        className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
        onSubmit={(event) => event.preventDefault()}
      >
        <label className="block">
          <span className="text-sm text-muted">Search</span>
          <input
            className={`${inputClass} mt-1`}
            value={searchInput}
            onChange={(event) => {
              setSearchInput(event.target.value)
              setPage(1)
            }}
            placeholder="Company or role"
          />
        </label>
        <label className="block">
          <span className="text-sm text-muted">Company</span>
          <input
            className={`${inputClass} mt-1`}
            value={companyInput}
            onChange={(event) => {
              setCompanyInput(event.target.value)
              setPage(1)
            }}
          />
        </label>
        <label className="block">
          <span className="text-sm text-muted">Status</span>
          <select
            className={`${inputClass} mt-1`}
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value)
              setPage(1)
            }}
          >
            <option value="">All statuses</option>
            {APPLICATION_STATUSES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-sm text-muted">Deadline after</span>
          <input
            className={`${inputClass} mt-1`}
            type="date"
            value={deadlineAfter}
            onChange={(event) => {
              setDeadlineAfter(event.target.value)
              setPage(1)
            }}
          />
        </label>
        <label className="block">
          <span className="text-sm text-muted">Deadline before</span>
          <input
            className={`${inputClass} mt-1`}
            type="date"
            value={deadlineBefore}
            onChange={(event) => {
              setDeadlineBefore(event.target.value)
              setPage(1)
            }}
          />
        </label>
        <label className="block">
          <span className="text-sm text-muted">Sort by</span>
          <select
            className={`${inputClass} mt-1`}
            value={sort}
            onChange={(event) => {
              setSort(event.target.value)
              setPage(1)
            }}
          >
            {APPLICATION_SORT_FIELDS.map((field) => (
              <option key={field.value} value={field.value}>
                {field.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <span className="text-sm text-muted">Sort order</span>
          <select
            className={`${inputClass} mt-1`}
            value={order}
            onChange={(event) => {
              setOrder(event.target.value)
              setPage(1)
            }}
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </label>
        <label className="block">
          <span className="text-sm text-muted">Page size</span>
          <select
            className={`${inputClass} mt-1`}
            value={pageSize}
            onChange={(event) => {
              setPageSize(Number(event.target.value))
              setPage(1)
            }}
          >
            {PAGE_SIZE_OPTIONS.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </label>
      </form>

      {hasActiveFilters ? (
        <Button className="mt-4" variant="ghost" type="button" onClick={clearFilters}>
          Clear filters
        </Button>
      ) : null}

      {status === 'loading' ? (
        <div className="mt-8">
          <LoadingState message="Loading applications…" />
        </div>
      ) : null}

      {status === 'error' ? (
        <div className="mt-8">
          <ErrorState message={error} onRetry={() => setReloadNonce((current) => current + 1)} />
        </div>
      ) : null}

      {status === 'ready' && items.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            title={hasActiveFilters ? 'No matching applications' : 'No applications yet'}
            message={
              hasActiveFilters
                ? 'Try a different search or clear the current filters.'
                : 'Create an application to start tracking jobs and internships.'
            }
            action={
              hasActiveFilters ? (
                <Button variant="secondary" type="button" onClick={clearFilters}>
                  Clear filters
                </Button>
              ) : (
                <Link className={buttonClass('primary')} to="/applications/new">
                  Create application
                </Link>
              )
            }
          />
        </div>
      ) : null}

      {status === 'ready' && items.length > 0 ? (
        <div className="mt-8 overflow-x-auto">
            <table className="min-w-[36rem] w-full text-left text-sm">
            <thead>
              <tr className="border-b border-line">
                <th className="py-2 pr-4 font-medium">Company</th>
                <th className="py-2 pr-4 font-medium">Role</th>
                <th className="py-2 pr-4 font-medium">Status</th>
                <th className="py-2 pr-4 font-medium">Deadline</th>
                <th className="py-2 pr-4 font-medium">Applied</th>
              </tr>
            </thead>
            <tbody>
              {items.map((application) => (
                <tr key={application.id} className="border-b border-line/70">
                  <td className="py-3 pr-4">
                    <Link
                      className="underline underline-offset-4 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
                      to={`/applications/${application.id}`}
                    >
                      {application.company_name}
                    </Link>
                  </td>
                  <td className="py-3 pr-4">{application.role_title}</td>
                  <td className="py-3 pr-4">
                    <StatusBadge status={application.status} />
                  </td>
                  <td className="py-3 pr-4">{formatDate(application.deadline)}</td>
                  <td className="py-3 pr-4">{formatDate(application.applied_date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {status === 'ready' ? (
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm text-muted">
          <p>
            Page {Math.min(page, totalPages)} of {totalPages} · {total} total
          </p>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              type="button"
              disabled={!canPrevious}
              onClick={() => setPage((current) => Math.max(1, current - 1))}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              type="button"
              disabled={!canNext}
              onClick={() => setPage((current) => current + 1)}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </Page>
  )
}

export default ApplicationsPage

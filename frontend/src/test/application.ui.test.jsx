import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import App from '../App'
import {
  emptyAnalyticsSummary,
  installApiMock,
  sampleApplication,
  sampleApplicationList,
  sampleInterview,
  sampleUser,
  tokenPayload,
} from './mockApi'

function renderApp(path, extraHandlers = {}) {
  window.localStorage.setItem('applylens.refresh_token', 'refresh-token')
  const mock = installApiMock({
    'post /api/v1/auth/refresh': () => ({ status: 200, data: tokenPayload() }),
    'get /api/v1/auth/me': () => ({ status: 200, data: sampleUser }),
    ...extraHandlers,
  })
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  )
  return mock
}

function applicationHandlers(application = sampleApplication(), interviews = []) {
  return {
    'get /api/v1/applications/1': () => ({ status: 200, data: application }),
    'get /api/v1/applications/1/interviews': () => ({ status: 200, data: interviews }),
  }
}

describe('dashboard analytics', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('loads analytics from the summary API', async () => {
    renderApp('/', {
      'get /api/v1/analytics/summary': () => ({
        status: 200,
        data: {
          ...emptyAnalyticsSummary,
          total_applications: 4,
          counts_by_status: {
            ...emptyAnalyticsSummary.counts_by_status,
            Applied: 2,
            Offer: 1,
            Rejected: 1,
          },
          upcoming_deadlines: 2,
          interview_count: 3,
          offers: 1,
          rejections: 1,
          response_rate: 0.5,
          average_time_to_response_days: null,
        },
      }),
      'get /api/v1/applications': () => ({
        status: 200,
        data: sampleApplicationList([sampleApplication()]),
      }),
    })

    expect(await screen.findByText('4')).toBeInTheDocument()
    expect(screen.getByText('Upcoming deadlines').parentElement).toHaveTextContent('2')
    expect(screen.getByText('Interview count').parentElement).toHaveTextContent('3')
    expect(screen.getByText('Offers').parentElement).toHaveTextContent('1')
    expect(screen.getByText('Rejections').parentElement).toHaveTextContent('1')
    expect(screen.getByText('50%')).toBeInTheDocument()
    expect(screen.getByText('Not available')).toBeInTheDocument()
    expect(screen.getByText('Acme')).toBeInTheDocument()
    expect(screen.queryByText(/no applications yet/i)).not.toBeInTheDocument()
  })

  it('shows an analytics error state', async () => {
    renderApp('/', {
      'get /api/v1/analytics/summary': () => ({
        status: 500,
        data: { detail: 'Analytics unavailable' },
      }),
    })

    expect(await screen.findByRole('alert')).toHaveTextContent('Analytics unavailable')
    expect(screen.queryByText('Total applications')).not.toBeInTheDocument()
  })
})

describe('applications list', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('loads applications from the API', async () => {
    const { requests } = renderApp('/applications', {
      'get /api/v1/applications': () => ({
        status: 200,
        data: sampleApplicationList([sampleApplication()]),
      }),
    })

    expect(await screen.findByRole('link', { name: 'Acme' })).toBeInTheDocument()
    expect(screen.getByText('Engineer')).toBeInTheDocument()
    expect(screen.getByText('2026-02-01')).toBeInTheDocument()
    expect(screen.getByText('2026-01-15')).toBeInTheDocument()
    expect(
      requests.some(
        (request) =>
          request.path === '/api/v1/applications' &&
          request.params.page === 1 &&
          request.params.page_size === 20,
      ),
    ).toBe(true)
  })

  it('shows an empty state when there are no applications', async () => {
    renderApp('/applications')

    expect(await screen.findByRole('heading', { name: /no applications yet/i })).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('does not show the empty state while the list is loading', async () => {
    let resolveList
    renderApp('/applications', {
      'get /api/v1/applications': () =>
        new Promise((resolve) => {
          resolveList = resolve
        }),
    })

    expect(await screen.findByText(/loading applications/i)).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /no applications yet/i })).not.toBeInTheDocument()

    resolveList({
      status: 200,
      data: sampleApplicationList([]),
    })

    expect(await screen.findByRole('heading', { name: /no applications yet/i })).toBeInTheDocument()
  })

  it('sends search to the backend after debounce', async () => {
    const user = userEvent.setup()
    const { requests } = renderApp('/applications', {
      'get /api/v1/applications': (config) => ({
        status: 200,
        data: sampleApplicationList(
          config.params?.search ? [sampleApplication()] : [],
        ),
      }),
    })

    await screen.findByRole('heading', { name: /applications/i })
    const initialCount = requests.filter((request) => request.path === '/api/v1/applications').length

    await user.type(screen.getByLabelText('Search'), 'Acme')

    await waitFor(() => {
      expect(
        requests.some(
          (request) => request.path === '/api/v1/applications' && request.params.search === 'Acme',
        ),
      ).toBe(true)
    })

    const listCalls = requests.filter((request) => request.path === '/api/v1/applications')
    expect(listCalls.length).toBeLessThan(initialCount + 4)
    expect(await screen.findByRole('link', { name: 'Acme' })).toBeInTheDocument()
  })

  it('filters by status, company, and deadlines via query parameters', async () => {
    const user = userEvent.setup()
    const { requests } = renderApp('/applications', {
      'get /api/v1/applications': () => ({
        status: 200,
        data: sampleApplicationList([sampleApplication({ status: 'Offer' })]),
      }),
    })

    await screen.findByRole('heading', { name: /applications/i })

    await user.selectOptions(screen.getByLabelText('Status'), 'Offer')
    fireEvent.change(screen.getByLabelText('Deadline after'), { target: { value: '2026-01-01' } })
    fireEvent.change(screen.getByLabelText('Deadline before'), { target: { value: '2026-03-01' } })
    await user.type(screen.getByLabelText('Company'), 'Acme')

    await waitFor(() => {
      expect(
        requests.some(
          (request) =>
            request.path === '/api/v1/applications' &&
            request.params.status === 'Offer' &&
            request.params.company === 'Acme' &&
            request.params.deadline_after === '2026-01-01' &&
            request.params.deadline_before === '2026-03-01',
        ),
      ).toBe(true)
    })
  })

  it('sends sort and pagination parameters to the backend', async () => {
    const user = userEvent.setup()
    const { requests } = renderApp('/applications', {
      'get /api/v1/applications': (config) => ({
        status: 200,
        data: sampleApplicationList([sampleApplication()], {
          page: Number(config.params?.page || 1),
          page_size: Number(config.params?.page_size || 20),
          total: 25,
        }),
      }),
    })

    await screen.findByRole('link', { name: 'Acme' })

    await user.selectOptions(screen.getByLabelText('Sort by'), 'deadline')
    await user.selectOptions(screen.getByLabelText('Sort order'), 'Ascending')
    await user.click(screen.getByRole('button', { name: /next/i }))

    await waitFor(() => {
      expect(
        requests.some(
          (request) =>
            request.path === '/api/v1/applications' &&
            request.params.sort === 'deadline' &&
            request.params.order === 'asc' &&
            request.params.page === 2,
        ),
      ).toBe(true)
    })
  })

  it('shows a no-results state for an unmatched filter', async () => {
    const user = userEvent.setup()
    renderApp('/applications', {
      'get /api/v1/applications': (config) => ({
        status: 200,
        data: sampleApplicationList(config.params?.status ? [] : [sampleApplication()]),
      }),
    })

    await screen.findByRole('link', { name: 'Acme' })
    await user.selectOptions(screen.getByLabelText('Status'), 'Rejected')

    expect(await screen.findByRole('heading', { name: /no matching applications/i })).toBeInTheDocument()
  })

  it('shows an application list error state', async () => {
    renderApp('/applications', {
      'get /api/v1/applications': () => ({
        status: 500,
        data: { detail: 'List failed' },
      }),
    })

    expect(await screen.findByRole('alert')).toHaveTextContent('List failed')
  })

  it('keeps the applications route protected', async () => {
    window.localStorage.clear()
    installApiMock({})
    render(
      <MemoryRouter initialEntries={['/applications']}>
        <App />
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: /log in/i })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /^applications$/i })).not.toBeInTheDocument()
  })
})

describe('application create, edit, detail, and delete', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('creates an application and shows it on the detail page', async () => {
    const user = userEvent.setup()
    const created = sampleApplication()
    const { requests } = renderApp('/applications/new', {
      'post /api/v1/applications': () => ({ status: 201, data: created }),
      ...applicationHandlers(created),
    })

    await user.type(await screen.findByLabelText('Company'), 'Acme')
    await user.type(screen.getByLabelText('Role'), 'Engineer')
    await user.selectOptions(screen.getByLabelText('Status'), 'Applied')
    await user.click(screen.getByRole('button', { name: /create application/i }))

    await waitFor(() => {
      expect(requests.some((request) => request.method === 'post' && request.path === '/api/v1/applications')).toBe(
        true,
      )
    })
    expect(await screen.findByRole('heading', { name: 'Acme' })).toBeInTheDocument()
    expect(screen.getByText('Engineer')).toBeInTheDocument()
    expect(screen.getByText('Build things')).toBeInTheDocument()
  })

  it('shows client-side and API create errors', async () => {
    const user = userEvent.setup()
    const { requests } = renderApp('/applications/new', {
      'post /api/v1/applications': () => ({
        status: 422,
        data: { detail: 'company_name must not be blank' },
      }),
    })

    await user.click(await screen.findByRole('button', { name: /create application/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Company is required.')
    expect(requests.some((request) => request.method === 'post' && request.path === '/api/v1/applications')).toBe(
      false,
    )

    await user.type(screen.getByLabelText('Company'), 'Acme')
    await user.type(screen.getByLabelText('Role'), 'Engineer')
    await user.click(screen.getByRole('button', { name: /create application/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('company_name must not be blank')
  })

  it('edits an application with a partial PUT', async () => {
    const user = userEvent.setup()
    const original = sampleApplication()
    const updated = sampleApplication({ notes: 'Updated notes', status: 'Interviewing' })
    const { requests } = renderApp('/applications/1/edit', {
      ...applicationHandlers(original),
      'put /api/v1/applications/1': () => ({ status: 200, data: updated }),
      'get /api/v1/applications/1': () => ({ status: 200, data: original }),
    })

    const notes = await screen.findByLabelText('Notes')
    await user.clear(notes)
    await user.type(notes, 'Updated notes')
    await user.selectOptions(screen.getByLabelText('Status'), 'Interviewing')
    await user.click(screen.getByRole('button', { name: /save changes/i }))

    await waitFor(() => {
      const put = requests.find((request) => request.method === 'put' && request.path === '/api/v1/applications/1')
      expect(put).toBeTruthy()
      expect(put.data).toEqual({ notes: 'Updated notes', status: 'Interviewing' })
    })
  })

  it('shows application detail and a not-found error', async () => {
    renderApp('/applications/1', applicationHandlers())

    expect(await screen.findByRole('heading', { name: 'Acme' })).toBeInTheDocument()
    expect(screen.getByText('Follow up')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /back to applications/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /edit/i })).toHaveAttribute('href', '/applications/1/edit')
  })

  it('shows an application API error on detail', async () => {
    renderApp('/applications/1', {
      'get /api/v1/applications/1': () => ({
        status: 404,
        data: { detail: 'Application not found' },
      }),
    })

    expect(await screen.findByRole('alert')).toHaveTextContent('Application not found.')
  })

  it('asks for confirmation before deleting an application', async () => {
    const user = userEvent.setup()
    const { requests } = renderApp('/applications/1', applicationHandlers())

    await screen.findByRole('heading', { name: 'Acme' })
    await user.click(screen.getByRole('button', { name: /^delete$/i }))

    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveTextContent(/this application and its interview rounds will be deleted/i)
    expect(requests.some((request) => request.method === 'delete')).toBe(false)

    await user.click(within(dialog).getByRole('button', { name: /cancel/i }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Acme' })).toBeInTheDocument()
  })

  it('deletes an application after confirmation and returns to the list', async () => {
    const user = userEvent.setup()
    let deleted = false
    const { requests } = renderApp('/applications/1', {
      ...applicationHandlers(),
      'delete /api/v1/applications/1': () => {
        deleted = true
        return { status: 204, data: '' }
      },
      'get /api/v1/applications': () => ({
        status: 200,
        data: sampleApplicationList(deleted ? [] : [sampleApplication()]),
      }),
    })

    await screen.findByRole('heading', { name: 'Acme' })
    await user.click(screen.getByRole('button', { name: /^delete$/i }))
    await user.click(screen.getByRole('button', { name: /delete application/i }))

    expect(await screen.findByRole('heading', { name: /no applications yet/i })).toBeInTheDocument()
    expect(requests.some((request) => request.method === 'delete' && request.path === '/api/v1/applications/1')).toBe(
      true,
    )
  })
})

describe('interview round UI', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('lists interview rounds on the application detail page', async () => {
    renderApp('/applications/1', applicationHandlers(sampleApplication(), [sampleInterview()]))

    expect(await screen.findByText('Phone screen')).toBeInTheDocument()
    expect(screen.getByText(/outcome: pending/i)).toBeInTheDocument()
  })

  it('creates an interview round', async () => {
    const user = userEvent.setup()
    const created = sampleInterview({ id: 11, round_name: 'Onsite' })
    const { requests } = renderApp('/applications/1', {
      ...applicationHandlers(sampleApplication(), []),
      'post /api/v1/applications/1/interviews': () => ({ status: 201, data: created }),
    })

    await screen.findByRole('button', { name: /add interview round/i })
    await user.click(screen.getByRole('button', { name: /add interview round/i }))
    await user.type(screen.getByLabelText('Round name'), 'Onsite')
    await user.click(screen.getByRole('button', { name: /create round/i }))

    expect(await screen.findByText('Onsite')).toBeInTheDocument()
    const post = requests.find(
      (request) => request.method === 'post' && request.path === '/api/v1/applications/1/interviews',
    )
    expect(post.data.round_name).toBe('Onsite')
    expect(post.data.outcome).toBe('Pending')
  })

  it('edits an interview round with a partial PUT', async () => {
    const user = userEvent.setup()
    const original = sampleInterview()
    const { requests } = renderApp('/applications/1', {
      ...applicationHandlers(sampleApplication(), [original]),
      'put /api/v1/applications/1/interviews/10': () => ({
        status: 200,
        data: sampleInterview({ outcome: 'Passed' }),
      }),
    })

    await screen.findByText('Phone screen')
    await user.click(screen.getByRole('button', { name: /^edit$/i }))
    await user.selectOptions(screen.getByLabelText('Outcome'), 'Passed')
    await user.click(screen.getByRole('button', { name: /save round/i }))

    await waitFor(() => {
      const put = requests.find(
        (request) => request.method === 'put' && request.path === '/api/v1/applications/1/interviews/10',
      )
      expect(put.data).toEqual({ outcome: 'Passed' })
    })
    expect(await screen.findByText(/outcome: passed/i)).toBeInTheDocument()
  })

  it('deletes an interview round after confirmation', async () => {
    const user = userEvent.setup()
    const { requests } = renderApp('/applications/1', {
      ...applicationHandlers(sampleApplication(), [sampleInterview()]),
      'delete /api/v1/applications/1/interviews/10': () => ({ status: 204, data: '' }),
    })

    await screen.findByText('Phone screen')
    const interviewItem = screen.getByText('Phone screen').closest('li')
    await user.click(within(interviewItem).getByRole('button', { name: /^delete$/i }))
    expect(screen.getByRole('dialog')).toHaveTextContent(/phone screen/i)
    expect(requests.some((request) => request.method === 'delete')).toBe(false)

    await user.click(screen.getByRole('button', { name: /delete round/i }))

    expect(await screen.findByRole('heading', { name: /no interview rounds yet/i })).toBeInTheDocument()
    expect(
      requests.some(
        (request) => request.method === 'delete' && request.path === '/api/v1/applications/1/interviews/10',
      ),
    ).toBe(true)
  })
})

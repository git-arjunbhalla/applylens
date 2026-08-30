import { useAuth } from '../hooks/useAuth'

function HomePage() {
  const { user, logout } = useAuth()

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="text-3xl font-semibold text-neutral-900">ApplyLens</h1>
      <p className="mt-3 text-neutral-600">You are signed in as {user.email}.</p>
      <button
        className="mt-8 rounded border border-neutral-300 px-3 py-2 text-neutral-900"
        type="button"
        onClick={logout}
      >
        Log out
      </button>
    </main>
  )
}

export default HomePage

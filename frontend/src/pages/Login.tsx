import { useState, type FormEvent } from 'react'
import { FileCheck2, LoaderCircle, CircleAlert } from 'lucide-react'
import { setCredentials, api } from '../api'

export function Login({ onLogin }: { onLogin: () => void }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!password.trim()) return
    setBusy(true)
    setError('')
    setCredentials('yesrole', password)
    try {
      await api.capabilities()
      onLogin()
    } catch {
      setError('Incorrect password. Please try again.')
      setBusy(false)
    }
  }

  return (
    <div className="login-shell">
      <div className="login-card">
        <div className="login-brand">
          <span className="logo"><FileCheck2 size={22} strokeWidth={2.2} /></span>
          <span className="login-brand-name">Yes<span>Role</span></span>
        </div>
        <div className="login-heading">
          <h1>Welcome back</h1>
          <p>Enter the demo password to access YesRole.</p>
        </div>
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="Enter demo password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoFocus
              autoComplete="current-password"
              disabled={busy}
            />
          </div>
          {error && (
            <div className="login-error" role="alert">
              <CircleAlert size={16} />
              {error}
            </div>
          )}
          <button className="button primary login-btn" type="submit" disabled={busy || !password.trim()}>
            {busy ? <><LoaderCircle size={17} className="spin" /> Signing in…</> : 'Sign in'}
          </button>
        </form>
        <p className="login-hint">Username: <code>yesrole</code></p>
      </div>
    </div>
  )
}

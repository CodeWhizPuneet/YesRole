import { lazy, Suspense, useState, type FormEvent } from 'react'
import { Activity, CircleCheck, ClipboardList, FileText, FlaskConical, History as HistoryIcon, LockKeyhole, Plus, ScanLine, Sparkles, Target, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api, errorMessage, hostedDemo } from '../api'
import { Empty, Feedback, PageHeading, PrimaryLink, ReportTable, useRemote } from '../components'
import { clearBrowserData, displayDate, forgetContext, getResumes, saveResume, writeResumes } from '../storage'

const TrendChart = lazy(() => import('./TrendChart'))

export function Dashboard() {
  const { data, error } = useRemote(api.history, 'dashboard')
  const rows = data ?? []
  const revised = rows.filter(row => row.change !== null)
  const mean = rows.length ? Math.round(rows.reduce((sum, row) => sum + row.score, 0) / rows.length) : null
  const stats = [
    { title: 'Total analyses', value: data ? String(rows.length) : '—', detail: 'Saved reports', Icon: ClipboardList, color: 'teal' },
    { title: 'Average match score', value: mean === null ? '—' : mean + '%', detail: 'Across saved reports', Icon: Target, color: 'blue' },
    { title: 'Requirements covered', value: data ? String(rows.reduce((sum, row) => sum + row.supported, 0)) : '—', detail: 'Fully supported in reports', Icon: CircleCheck, color: 'violet' },
    { title: 'Recent improvements', value: data ? String(revised.filter(row => (row.change ?? 0) > 0).length) : '—', detail: 'Revisions with higher scores', Icon: TrendingUp, color: 'amber' },
  ]
  const trend = rows.slice(0, 12).reverse().map(row => ({ date: displayDate(row.created_at), score: row.score, role: row.title }))
  return <>
    <PageHeading title="Dashboard" description="Your resume analysis workspace." />
    <section className="welcome">
      <div className="welcome-copy">
        <div className="eyebrow"><span /> Resume intelligence</div>
        <h2>Your Next Opportunity<br className="wide-break" /> Starts Here.</h2>
        <p>Align your experience with the right role.</p>
        <div className="actions"><PrimaryLink /><Link className="button secondary" to="/new?demo=0"><FlaskConical size={17} />Try Demo</Link></div>
      </div>
      <div className="hero-art" aria-hidden="true">
        <div className="hero-orbit orbit-one" /><div className="hero-orbit orbit-two" />
        <div className="hero-doc"><div className="hero-doc-icon"><FileText size={20} /></div><i /><i /><i /><i /><i /></div>
        <div className="hero-check"><CircleCheck size={29} strokeWidth={1.7} /></div>
        <div className="hero-spark"><Sparkles size={20} strokeWidth={1.7} /></div>
      </div>
    </section>
    <Feedback error={error} busy={!data && !error ? 'Loading saved analyses…' : undefined} />
    <div className="stat-grid">{stats.map(({ title, value, detail, Icon, color }) =>
      <article className="card stat" key={title}>
        <div className="stat-top"><span>{title}</span><span className={'icon-tile ' + color}><Icon size={19} /></span></div>
        <strong>{value}</strong><small>{detail}</small>
      </article>)}</div>
    <div className="dashboard-grid">
      <section className="card trend"><div className="card-head"><div><h2>Match score trends</h2><p>Your latest YesRole Match Scores.</p></div><Activity size={20} /></div>
        {trend.length ? <Suspense fallback={<div className="trend-chart" aria-label="Loading chart" />}><TrendChart data={trend} /></Suspense>
          : <Empty title={error ? 'Scores unavailable' : 'Your trend starts here'} detail={error ? 'Saved scores could not be loaded.' : 'Run an analysis to see your match scores here.'} />}
      </section>
      <section className="card quick"><div className="card-head"><div><h2>Quick actions</h2><p>Pick up where you left off.</p></div></div>
        {[
          { title: 'New analysis', detail: 'Compare a resume with a role', to: '/new', Icon: ScanLine },
          { title: 'My resumes', detail: 'Open your saved versions', to: '/resumes', Icon: FileText },
          { title: 'Analysis history', detail: 'Review your previous reports', to: '/history', Icon: HistoryIcon },
        ].map(({ title, detail, to, Icon }) => <Link className="quick-link" key={to} to={to}>
          <span className="icon-tile"><Icon size={19} /></span><span><strong>{title}</strong><small>{detail}</small></span>
        </Link>)}
      </section>
    </div>
    <section className="card"><div className="card-head"><div><h2>Recent analyses</h2><p>Return to the roles you’ve reviewed.</p></div><Link className="text-button" to="/history">View history</Link></div>
      {rows.length ? <ReportTable rows={rows.slice(0, 5)} /> : <Empty title={error ? 'Reports unavailable' : 'No analyses yet'} detail={error ? 'Saved reports could not be loaded.' : 'Upload a resume or try a fictional example to see your first report.'} />}
    </section>
  </>
}

export function History() {
  const [refresh, setRefresh] = useState(0)
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')
  const [deleting, setDeleting] = useState('')
  const { data, error: loadError } = useRemote(api.history, String(refresh))
  const rows = (data ?? []).filter(row => (row.title + ' ' + row.company + ' ' + row.version).toLowerCase().includes(query.trim().toLowerCase()))
  async function remove(id: string) {
    if (deleting || !window.confirm('Delete this saved report? Any comparison that depends on it will be unavailable.')) return
    setError('')
    setDeleting(id)
    try { await api.remove(id); forgetContext(id); setRefresh(value => value + 1) }
    catch (reason) { setError(errorMessage(reason)) }
    finally { setDeleting('') }
  }
  return <>
    <PageHeading title="Analysis History" description="Review past match reports and resume revisions."><PrimaryLink /></PageHeading>
    <Feedback error={error || loadError} busy={deleting ? 'Deleting report…' : !data && !loadError ? 'Loading reports…' : undefined} />
    <section className="card">
      <div className="card-head"><div><h2>Saved reports</h2><p>{data ? data.length + ' analyses on this device' : 'Local analysis history'}</p></div>
        <input type="search" placeholder="Search roles or companies" aria-label="Search analysis history" value={query} onChange={event => setQuery(event.target.value)} />
      </div>
      {rows.length ? <ReportTable rows={rows} onDelete={remove} /> : <Empty title={query ? 'No matching reports' : 'No reports to show'} detail={query ? 'Try another job title or company.' : 'Completed analyses appear here.'} />}
    </section>
  </>
}

export function Library() {
  const [resumes, setResumes] = useState(getResumes)
  const [editing, setEditing] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')

  function rename(event: FormEvent, id: string, text: string) {
    event.preventDefault()
    if (!name.trim()) return
    try { saveResume(name.trim(), text, id); setResumes(getResumes()); setEditing(''); setError('') }
    catch (reason) { setError(errorMessage(reason)) }
  }
  function remove(id: string) {
    if (!window.confirm('Delete this saved resume version from this browser?')) return
    try { writeResumes(resumes.filter(resume => resume.id !== id)); setResumes(getResumes()); setError('') }
    catch (reason) { setError(errorMessage(reason)) }
  }
  return <>
    <PageHeading title="My Resumes" description="Open and manage the versions you’ve saved in this browser."><PrimaryLink /></PageHeading>
    <Feedback error={error} />
    <section className="card"><div className="card-head"><div><h2>Saved versions</h2><p>{resumes.length} {resumes.length === 1 ? 'resume' : 'resumes'}</p></div></div>
      {resumes.length ? <div className="stack">{resumes.map(resume => <div className="list-row" key={resume.id}>
        <span className="icon-tile"><FileText size={19} /></span>
        {editing === resume.id ? <form className="actions grow" onSubmit={event => rename(event, resume.id, resume.text)}>
          <input autoFocus required maxLength={120} aria-label="Resume name" value={name} onChange={event => setName(event.target.value)} />
          <button className="button primary" type="submit">Save name</button><button className="button secondary" type="button" onClick={() => setEditing('')}>Cancel</button>
        </form> : <>
          <div className="grow"><strong>{resume.name}</strong><small>Updated {displayDate(resume.updatedAt)}</small></div>
          <div className="actions">
            <Link className="button secondary" to={'/studio?saved=' + resume.id}>Open</Link>
            <Link className="button secondary" to={'/new?saved=' + resume.id}><Plus size={15} />New analysis</Link>
            <button className="text-button" onClick={() => { setEditing(resume.id); setName(resume.name) }}>Rename</button>
            <button className="text-button danger" onClick={() => remove(resume.id)}>Delete</button>
          </div>
        </>}
      </div>)}</div> : <Empty title="No saved resume versions" detail="Open the Optimization Studio to edit and save a version."><Link className="button secondary" to="/studio">Open Studio</Link></Empty>}
    </section>
  </>
}

export function Settings() {
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  return <>
    <PageHeading title="Settings" description="Manage the information YesRole keeps on this device." />
    <Feedback error={error} />
    <div className="card settings">
      <div className="card-head"><div><h2><LockKeyhole size={20} /> Data and privacy</h2><p>{hostedDemo ? 'This is a shared, password-protected demo.' : 'YesRole is running in local demo mode.'}</p></div></div>
      <p>{hostedDemo ? 'The hosted server processes documents. Anyone with the demo password can view or delete report excerpts. Use fictional data only.' : 'Documents are processed by the local backend. Saved reports include quoted evidence, and you can delete each report in Analysis History.'}</p>
      <p>Saved resume versions stay in this browser. Your current tab also keeps working text for editing and comparison.</p>
      <div className="actions"><Link className="button secondary" to="/history">Manage reports</Link>
        <button className="button secondary danger" onClick={() => {
          if (!window.confirm('Clear saved resumes and working analysis text from this browser?')) return
          try { clearBrowserData(); setNotice('Browser resume versions and working text cleared.'); setError('') }
          catch (reason) { setError(errorMessage(reason)) }
        }}>Clear browser data</button></div>
      {notice && <p role="status" className="positive">{notice}</p>}
    </div>
  </>
}


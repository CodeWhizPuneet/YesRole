import { useEffect, useState, type ReactNode } from 'react'
import { CircleAlert, CircleCheck, FileCheck2, FileText, LoaderCircle, Plus } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api, errorMessage } from './api'
import { displayDate } from './storage'
import type { Analysis, Status, Summary } from './types'

export const tone = (status: Status | 'Pass' | 'Warning' | 'Issue') => ({
  Supported: 'good', 'Partially Supported': 'amber', 'Not Evidenced': 'negative',
  Pass: 'good', Warning: 'amber', Issue: 'negative',
}[status])

export function Brand() {
  return <Link className="brand" to="/" aria-label="YesRole dashboard">
    <span className="logo"><FileCheck2 size={22} strokeWidth={2.2} /></span><span>Yes<span>Role</span></span>
  </Link>
}

export function PrimaryLink({ to = '/new', children = 'Analyze New Resume' }: { to?: string; children?: ReactNode }) {
  return <Link className="button primary" to={to}><Plus size={18} />{children}</Link>
}
export function Feedback({ error, busy }: { error?: string; busy?: string }) {
  return <>
    {error && <div className="feedback error" role="alert"><CircleAlert size={18} />{error}</div>}
    {busy && <div className="feedback" role="status"><LoaderCircle className="spin" size={18} />{busy}</div>}
  </>
}
export function Empty({ title, detail, children }: { title: string; detail: string; children?: ReactNode }) {
  return <div className="empty"><span className="icon-tile"><FileText size={22} /></span>
    <strong>{title}</strong><p>{detail}</p>{children}</div>
}
export function PageHeading({ title, description, children }: { title: string; description: string; children?: ReactNode }) {
  return <div className="page-heading"><div><h1>{title}</h1><p>{description}</p></div>{children}</div>
}
export function useRemote<T>(load: () => Promise<T>, key: string) {
  const [state, setState] = useState<{ key: string; data?: T; error?: string }>({ key })
  useEffect(() => {
    let active = true
    load().then(data => { if (active) setState({ key, data }) }, error => {
      if (active) setState({ key, error: errorMessage(error) })
    })
    return () => { active = false }
  }, [key])
  return state.key === key ? state : { key }
}
export function useReport(id: string) {
  return useRemote(() => api.report(id), id)
}
export function CountChecks({ checks }: { checks: Analysis['ats'] }) {
  return <span className="status good"><CircleCheck size={14} />{checks.filter(check => check.status === 'Pass').length} passed</span>
}
export function ReportTable({ rows, onDelete }: { rows: Summary[]; onDelete?: (id: string) => void }) {
  return <div className="table-scroll"><table><thead><tr>
    <th>Target role</th><th>Resume version</th><th>Date</th><th>Match score</th><th>Actions</th>
  </tr></thead><tbody>{rows.map(row => <tr key={row.id}>
    <td><strong>{row.title}</strong>{row.company && <small>{row.company}</small>}</td>
    <td>{row.version}</td><td>{displayDate(row.created_at)}</td><td><span className="status good">{row.score}/100</span></td>
    <td><div className="actions"><Link className="text-button" to={'/analysis/' + row.id}>View report</Link>
      {onDelete && <button className="text-button danger" onClick={() => onDelete(row.id)} aria-label={'Delete analysis for ' + row.title}>Delete</button>}
    </div></td>
  </tr>)}</tbody></table></div>
}


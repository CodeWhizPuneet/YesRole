import { useState } from 'react'
import { BookOpen, ChevronDown, CircleCheck, CircleDashed, CircleX, Download, FileCheck2, Pencil, RotateCw, Sparkles } from 'lucide-react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { download } from '../api'
import { CountChecks, Empty, Feedback, PageHeading, tone, useReport } from '../components'
import { displayDate } from '../storage'
import { statuses, type Analysis, type Check, type Finding, type Status } from '../types'

const statusIcons = { Supported: CircleCheck, 'Partially Supported': CircleDashed, 'Not Evidenced': CircleX }

export function Readability({ checks }: { checks: Check[] }) {
  return <div className="check-grid">{checks.map((item, index) => <div className="check" key={item.name + index}>
    <div><strong>{item.name}</strong><span className={'status ' + tone(item.status)}>{item.status}</span></div><p>{item.detail}</p>
  </div>)}</div>
}

function EvidenceRow({ finding }: { finding: Finding }) {
  const Icon = statusIcons[finding.status]
  return <details className="evidence">
    <summary><Icon size={18} className={tone(finding.status)} /><span><strong>{finding.requirement.text}</strong>
      <small>{finding.requirement.priority} · {finding.requirement.category}</small></span>
      <span className={'status ' + tone(finding.status)}>{finding.status}</span><ChevronDown size={17} />
    </summary>
    <div className="evidence-body">
      <p>{finding.explanation}</p>
      {finding.requirement.skills.length > 0 && <p>Named skills · {finding.requirement.skills.join(', ')}</p>}
      {finding.evidence ? [finding.evidence, ...(finding.additional_evidence ?? [])].map((passage, index) =>
        <blockquote key={index}><small>{finding.status === 'Not Evidenced' ? 'Closest passage' : 'Resume evidence'} · {passage.section} · Cosine similarity {passage.similarity.toFixed(2)}</small>
          <p>{passage.text}</p></blockquote>) : <p>No relevant passage retrieved.</p>}
    </div>
  </details>
}

function exportReport(data: Analysis) {
  const sections = [
    'YesRole Match Report', data.title + (data.company ? ' at ' + data.company : ''), displayDate(data.created_at),
    'YesRole Match Score: ' + data.score + '/100',
    ...data.dimensions.map(item => item.name + ': ' + item.value + '% (effective weight ' + item.weight + '%)'),
    'Requirement evidence', ...data.findings.map(item => [
      item.requirement.text, item.requirement.priority + ' · ' + item.status, item.explanation,
      item.evidence ? item.evidence.section + ': ' + item.evidence.text + ' (cosine ' + item.evidence.similarity + ')' : '',
      ...(item.additional_evidence ?? []).map(item => item.section + ': ' + item.text + ' (cosine ' + item.similarity + ')'),
    ].filter(Boolean).join('\n')),
    'ATS readability', ...data.ats.map(item => item.name + ' · ' + item.status + '\n' + item.detail),
    'Recommendations', ...data.suggestions.map(item => item.kind + ' · ' + item.title + '\n' + item.detail +
      (item.replacement ? '\nProposed text: ' + item.replacement : '')),
  ]
  download(new Blob([sections.join('\n\n')], { type: 'text/plain;charset=utf-8' }), 'yesrole-match-report.txt')
}

export function Report() {
  const { id = '' } = useParams()
  const location = useLocation()
  const { data, error } = useReport(id)
  const [filter, setFilter] = useState<'All' | Status>('All')
  if (!data) return <Feedback error={error} busy={error ? undefined : 'Loading analysis report…'} />
  const findings = data.findings.filter(item => filter === 'All' || item.status === filter)
  return <>
    <PageHeading title={data.title} description={[data.company, data.version, displayDate(data.created_at)].filter(Boolean).join(' · ')}>
      <div className="actions"><button className="button secondary" onClick={() => exportReport(data)}><Download size={17} />Export report</button>
        <Link className="button primary" to={'/studio/' + id}><Sparkles size={17} />Optimize Resume</Link>
      </div>
    </PageHeading>
    {location.state?.contextUnavailable && <Feedback error="The report was saved. Browser storage was unavailable, so paste the resume and job description in Studio to continue." />}
    <div className="report-top">
      <section className="card score-card">
        <h2>YesRole Match Score</h2>
        <div className="score-ring" style={{ background: 'conic-gradient(var(--teal) ' + data.score + '%, var(--border) 0)' }}>
          <div><strong>{data.score}</strong><small>out of 100</small></div>
        </div>
        <p>How clearly your resume evidences this role’s requirements.</p>
        <div className="actions"><Link className="text-button" to={'/studio/' + id + '?edit=1'}><Pencil size={15} /> Edit resume</Link>
          <Link className="text-button" to={'/studio/' + id + '?edit=1#reanalyze'}><RotateCw size={15} /> Reanalyze</Link></div>
        {data.parent_id && <Link className="button secondary" to={'/compare/' + id}>View before &amp; after</Link>}
      </section>
      <section className="card dimensions">
        <div className="card-head"><div><h2>Dimension breakdown</h2><p>Effective weights reflect the requirements in this job description.</p></div></div>
        {data.dimensions.map(item => <div className="dimension" key={item.name}>
          <div><span>{item.name} <small>· {item.weight}% weight</small></span><strong>{item.value}%</strong></div>
          <progress value={item.value} max={100} aria-label={item.name} />
        </div>)}
        <details className="method"><summary>How the score is calculated</summary>
          <p>Coverage gives 1 point for supported, 0.5 for partial, and 0 for unevidenced requirements. MiniLM cosine similarity contributes when evidence supports a requirement. Evidence quality rewards concrete work or project actions. The weighted average adjusts when a category is absent. This is a YesRole heuristic for resume alignment.</p></details>
      </section>
    </div>
    <section className="card"><div className="card-head"><div><h2>Requirement overview</h2><p>Select a classification to explore its evidence.</p></div></div>
      <div className="verification">{statuses.map(status => {
        const Icon = statusIcons[status]
        return <button className="mini-card" aria-pressed={filter === status} key={status} onClick={() => setFilter(filter === status ? 'All' : status)}>
          <Icon size={22} className={tone(status)} /><span>{status}</span><strong>{data.findings.filter(item => item.status === status).length}</strong>
        </button>
      })}</div>
    </section>
    <section className="card"><div className="card-head"><div><h2><BookOpen size={20} /> Evidence Explorer</h2><p>Expand a requirement to inspect the source passage and classification.</p></div>
      <select value={filter} aria-label="Filter by classification" onChange={event => setFilter(event.target.value as typeof filter)}>
        <option value="All">All requirements</option>{statuses.map(item => <option key={item}>{item}</option>)}
      </select></div>
      {findings.length ? <div className="stack">{filter === 'All' ? statuses.map(status => {
        const group = findings.filter(item => item.status === status)
        return group.length > 0 && <section className="evidence-group stack" key={status} aria-label={status}>
          <h3>{status}</h3>{group.map(item => <EvidenceRow key={item.requirement.id} finding={item} />)}
        </section>
      }) : findings.map(item => <EvidenceRow key={item.requirement.id} finding={item} />)}</div>
        : <Empty title="No requirements in this category" detail="Choose another filter to see more evidence." />}
    </section>
    <section className="card"><div className="card-head"><div><h2><FileCheck2 size={20} /> ATS Readability</h2><p>Document checks and formatting warnings are separate from the match score.</p></div><CountChecks checks={data.ats} /></div>
      <Readability checks={data.ats} />
    </section>
    <section className="card"><div className="card-head"><div><h2><Sparkles size={20} /> Improvement recommendations</h2><p>Address required gaps first, then review grounded wording suggestions.</p></div>
      <Link className="text-button" to={'/studio/' + id}>Open Studio</Link></div>
      {data.suggestions.length ? <div className="stack">{data.suggestions.map(item =>
        <div className="suggestion" key={item.id}><span className={'status ' + (item.kind === 'Safe Rephrasing' ? 'good' : 'amber')}>{item.kind}</span><strong>{item.title}</strong><p>{item.detail}</p></div>)}</div>
        : <Empty title="No additional suggestions" detail="Use Studio if you’d like to refine the wording or layout." />}
    </section>
  </>
}


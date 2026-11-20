import { useEffect, useRef, useState } from 'react'
import { Check, Download, FileText, Pencil, RefreshCw, RotateCcw, Save, Sparkles } from 'lucide-react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api, downloadResume, errorMessage } from '../api'
import { CountChecks, Empty, Feedback, PageHeading, PrimaryLink, useRemote, useReport } from '../components'
import { getContext, getResumes, saveResume, setContext } from '../storage'
import { statuses, type Analysis, type Status, type Suggestion } from '../types'
import { Readability } from './Report'

const headings = /^(?:contact|professional summary|summary|profile|objective|technical skills|skills|experience|work experience|professional experience|internships|projects|selected projects|education|certifications|awards|publications|volunteering):?$/gim
const validText = (value: string) => value.trim().length >= 30

function linesOnly(before: string, after: string) {
  const remaining = new Map<string, number>()
  before.split('\n').forEach(line => remaining.set(line, (remaining.get(line) ?? 0) + 1))
  return after.split('\n').filter(line => {
    const count = remaining.get(line) ?? 0
    if (count) remaining.set(line, count - 1)
    return !count && line.trim()
  })
}

function Changes({ original, revised }: { original: string; revised: string }) {
  const removed = linesOnly(revised, original)
  const added = linesOnly(original, revised)
  if (!added.length && !removed.length) {
    return <p className="muted">{original === revised ? 'No text changes yet.' : 'The same lines appear in a different order or spacing.'}</p>
  }
  return <div className="diff">
    {removed.map((line, index) => <div key={'removed-' + index} className="removed"><span aria-label="Removed">−</span>{line}</div>)}
    {added.map((line, index) => <div key={'added-' + index} className="added"><span aria-label="Added">+</span>{line}</div>)}
  </div>
}

function Editor({ report, initial, initialJob, name, autoFocus }: {
  report?: Analysis; initial: string; initialJob: string; name: string; autoFocus: boolean
}) {
  const [original, setOriginal] = useState(initial)
  const [draft, setDraft] = useState(initial)
  const [job, setJob] = useState(initialJob)
  const [version, setVersion] = useState(name)
  const [undo, setUndo] = useState<{ text: string; dismissed: string[] }[]>([])
  const [dismissed, setDismissed] = useState<string[]>([])
  const [priority, setPriority] = useState<Suggestion[]>([])
  const { data: capabilities } = useRemote(api.capabilities, 'capabilities')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState('')
  const editor = useRef<HTMLTextAreaElement>(null)
  const editStarted = useRef(false)
  const navigate = useNavigate()
  const { hash } = useLocation()
  useEffect(() => {
    if (hash === '#reanalyze') document.getElementById('reanalyze')?.scrollIntoView()
  }, [hash])
  const sectionLinks = [...draft.matchAll(headings)]
  const run = async (label: string, action: () => Promise<void>) => {
    setError('')
    setNotice('')
    setBusy(label)
    try { await action() }
    catch (reason) { setError(errorMessage(reason)) }
    finally { setBusy('') }
  }

  function checkpoint() {
    setUndo(items => [...items.slice(-39), { text: draft, dismissed }])
    editStarted.current = false
  }

  function accept(item: Suggestion) {
    if (!item.original || !item.replacement) return
    const lines = draft.split('\n')
    const index = lines.indexOf(item.original)
    if (index === -1) { setError('The original line was edited. Apply the wording manually if it still fits.'); return }
    checkpoint()
    lines[index] = item.replacement
    setDraft(lines.join('\n'))
    setDismissed(current => [...current, item.id])
    setNotice('Suggestion applied to your draft.')
    setError('')
  }

  const ranked = priority.length
    ? [...(report?.suggestions.filter(item => item.kind === 'Needs User Confirmation') ?? []), ...priority]
    : report?.suggestions ?? []
  const suggestions = ranked.filter(item => !dismissed.includes(item.id))
  return <>
    <PageHeading title="Optimization Studio" description={report ? 'Tailor your resume for ' + report.title + '.' : 'Edit your resume and export an approved version.'}>
      {report && <Link to={'/analysis/' + report.id} className="button secondary">Back to report</Link>}
    </PageHeading>
    <div className="studio-tools card">
      <label>Version name<input value={version} maxLength={120} onChange={event => setVersion(event.target.value)} /></label>
      <div className="actions">
        <button className="button secondary" disabled={!undo.length || !!busy} onClick={() => {
          const previous = undo.at(-1)
          if (!previous) return
          editStarted.current = false
          setDraft(previous.text); setDismissed(previous.dismissed); setUndo(items => items.slice(0, -1))
          setNotice('Last change undone.'); setError('')
        }}><RotateCcw size={16} />Undo</button>
        <button className="button primary" disabled={!!busy || !validText(draft) || !version.trim()} onClick={() => void run('Saving resume…', async () => {
          saveResume(version.trim(), draft)
          setNotice('Resume version saved in My Resumes.')
        })}><Save size={17} />Save version</button>
      </div>
    </div>
    <Feedback error={error} busy={busy} />
    {notice && <div className="feedback positive" role="status"><Check size={18} />{notice}</div>}
    <div className="two">
      <section className="card editor-panel"><div className="card-head"><div><h2><FileText size={20} /> Original resume</h2><p>{initial ? 'Your starting text for this revision.' : 'Paste the original to restore the comparison.'}</p></div></div>
        {initial ? <pre className="resume-preview">{original}</pre> : <label>Original resume text<textarea rows={16} maxLength={60000} value={original} onChange={event => {
          const value = event.target.value
          if (draft === original) setDraft(value)
          setOriginal(value)
        }} placeholder="Paste the original resume text here." /></label>}
      </section>
      <section className="card editor-panel"><div className="card-head"><div><h2><Pencil size={20} /> Editable resume</h2><p>Review and approve the text you plan to export.</p></div></div>
        {sectionLinks.length > 0 && <div className="section-links" aria-label="Resume sections">{sectionLinks.map(match => <button className="status" key={match.index} onClick={() => {
          editor.current?.focus()
          editor.current?.setSelectionRange(match.index, match.index + match[0].length)
        }}>{match[0]}</button>)}</div>}
        <label className="sr-only" htmlFor="resume-draft">Editable resume text</label>
        <textarea ref={editor} autoFocus={autoFocus && !hash} id="resume-draft" rows={17} maxLength={60000} value={draft} onChange={event => {
          if (!editStarted.current) { checkpoint(); editStarted.current = true }
          setDraft(event.target.value)
        }} onBlur={() => { editStarted.current = false }} placeholder="Type or paste your resume." />
      </section>
    </div>
    <section className="card"><div className="card-head"><div><h2>Highlighted changes</h2><p>Lines added or removed since the original.</p></div></div><Changes original={original} revised={draft} /></section>
    {report && <section className="card"><div className="card-head"><div><h2><Sparkles size={20} /> Suggested improvements</h2><p>Review each suggestion before applying it.</p></div>
      {capabilities?.local_editor && suggestions.some(item => item.kind === 'Safe Rephrasing') &&
        <button className="button secondary" disabled={!!busy} onClick={() => {
          if (!window.confirm('Send the target requirements and proposed rephrasing text to your configured local model for ranking?')) return
          void run('Ranking suggested rewrites…', async () => {
            setPriority(await api.prioritize(report.id))
            setNotice('Grounded rewrites ranked by the local model.')
          })
        }}>Rank rewrites with local AI</button>}
      </div>
      {suggestions.length ? <div className="stack">{suggestions.map(item => <div className="suggestion" key={item.id}>
        <span className={'status ' + (item.kind === 'Safe Rephrasing' ? 'good' : 'amber')}>{item.kind}</span>
        <strong>{item.title}</strong><p>{item.detail}</p>
        {item.original && item.replacement && <Changes original={item.original} revised={item.replacement} />}
        <div className="actions">
          {item.replacement && <button className="button primary" disabled={!!busy} onClick={() => accept(item)}>Accept suggestion</button>}
          <button className="button secondary" disabled={!!busy} onClick={() => {
            checkpoint(); setDismissed(current => [...current, item.id])
          }}>Reject suggestion</button>
        </div>
      </div>)}</div> : <Empty title="No pending suggestions" detail="Continue editing or reanalyze your draft." />}
    </section>}
    <section className="card" id="reanalyze"><div className="card-head"><div><h2>Reanalyze and export</h2><p>Run a new match against the same role or download the current draft.</p></div></div>
      {report && !initialJob && <label>Original job description<textarea rows={5} value={job} maxLength={24000} onChange={event => setJob(event.target.value)} placeholder="Paste the same job description used in the original analysis." /></label>}
      <div className="actions">
        {report && <button className="button primary" type="button" disabled={!!busy || !validText(draft) || job.trim().length < 25}
          onClick={() => void run('Running MiniLM inference for your revised resume…', async () => {
            const updated = await api.reanalyze(report.id, draft, job.trim(), version.trim().length >= 2 ? version.trim() : 'Revised resume')
            setContext(updated.id, { resume: draft.trim(), description: job.trim() })
            if (!initial && validText(original)) setContext(report.id, { resume: original.trim(), description: job.trim() })
            navigate('/compare/' + updated.id, { state: { original, revised: draft } })
          })}><RefreshCw size={17} />Reanalyze resume</button>}
        {(['docx', 'pdf'] as const).map(format => <button key={format} className="button secondary" disabled={!!busy || !validText(draft)}
          onClick={() => void run('Formatting your resume…', async () => {
            await downloadResume(draft, format)
            setNotice('Resume downloaded as ' + format.toUpperCase() + '.')
          })}><Download size={17} />Export {format.toUpperCase()}</button>)}
      </div>
    </section>
  </>
}

function LinkedEditor({ id }: { id: string }) {
  const { data, error } = useReport(id)
  const [params] = useSearchParams()
  if (!data) return <Feedback error={error} busy={error ? undefined : 'Loading the analysis and suggestions…'} />
  const context = getContext(id)
  return <Editor report={data} initial={context?.resume ?? ''} initialJob={context?.description ?? ''} name="Revised resume" autoFocus={params.has('edit')} />
}

export function Studio() {
  const { id } = useParams()
  const [params] = useSearchParams()
  if (id) return <LinkedEditor id={id} />
  const saved = getResumes().find(item => item.id === params.get('saved'))
  return <Editor initial={saved?.text ?? ''} initialJob="" name={saved ? saved.name + ' copy' : 'My resume'} autoFocus={false} />
}

export function Compare() {
  const { id = '' } = useParams()
  const location = useLocation()
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState('')
  const { data: revised, error: revisedError } = useReport(id)
  const previous = revised?.parent_id
  const { data: original, error: originalError } = useRemote(() => previous ? api.report(previous) : Promise.resolve(null), previous ?? '')
  const error = revisedError || originalError
  if (revised && !previous) return <Empty title="No baseline for this report" detail="Reanalyze a resume to create a comparison."><PrimaryLink /></Empty>
  if (!revised || !original) return <Feedback error={error} busy={error ? undefined : 'Loading both analyses…'} />
  const delta = revised.score - original.score
  const deltaLabel = (value: number) => (value > 0 ? '+' : '') + value
  const baseText = getContext(original.id)?.resume || location.state?.original
  const revisedText = getContext(revised.id)?.resume || location.state?.revised
  const gaps = revised.findings.filter(item => item.status !== 'Supported')
  const count = (analysis: Analysis, status: Status) => analysis.findings.filter(item => item.status === status).length
  return <>
    <PageHeading title="Before & After" description={revised.title + ' · ' + revised.version}>
      <div className="actions"><Link className="button secondary" to={'/analysis/' + revised.id}>View revised report</Link>
        {revisedText ? (['docx', 'pdf'] as const).map(format => <button key={format} className="button secondary" disabled={exporting}
          onClick={async () => {
            setExportError('')
            setExporting(true)
            try { await downloadResume(revisedText, format) }
            catch (reason) { setExportError(errorMessage(reason)) }
            finally { setExporting(false) }
          }}><Download size={17} />Export {format.toUpperCase()}</button>)
          : <Link className="button secondary" to={'/studio/' + revised.id}>Open revised resume in Studio</Link>}</div>
    </PageHeading>
    <Feedback error={exportError} busy={exporting ? 'Formatting your resume…' : undefined} />
    <div className="comparison-stats">
      <div className="card"><small>Original match score</small><strong>{original.score}<span> / 100</span></strong><Link className="text-button" to={'/analysis/' + original.id}>View original report</Link></div>
      <div className="card"><small>Revised match score</small><strong>{revised.score}<span> / 100</span></strong><small>{count(revised, 'Supported')} of {revised.findings.length} requirements fully supported</small></div>
      <div className="card"><small>Match score change</small><strong className={delta > 0 ? 'good' : delta < 0 ? 'negative' : ''}>{deltaLabel(delta)}<span> points</span></strong><small>{deltaLabel(count(revised, 'Supported') - count(original, 'Supported'))} fully supported requirements</small></div>
    </div>
    <section className="card"><div className="card-head"><h2>Requirement coverage change</h2></div>
      <div className="table-scroll"><table><thead><tr><th>Classification</th><th>Original</th><th>Revised</th><th>Change</th></tr></thead>
        <tbody>{statuses.map(status => {
          const before = count(original, status)
          const after = count(revised, status)
          return <tr key={status}><th scope="row">{status}</th><td>{before}</td><td>{after}</td><td>{deltaLabel(after - before)}</td></tr>
        })}</tbody>
      </table></div>
    </section>
    <div className="two">
      <section className="card"><div className="card-head"><h2>Original ATS readability</h2><CountChecks checks={original.ats} /></div><Readability checks={original.ats} /></section>
      <section className="card"><div className="card-head"><h2>Revised ATS readability</h2><CountChecks checks={revised.ats} /></div><Readability checks={revised.ats} /></section>
    </div>
    <section className="card"><div className="card-head"><div><h2>Remaining evidence gaps</h2><p>Requirements still partially supported or not evidenced.</p></div></div>
      {gaps.length ? <ul className="gap-list">{gaps.map(item => <li key={item.requirement.id}><strong>{item.requirement.text}</strong><p>{item.status} · {item.explanation}</p></li>)}</ul> : <p className="muted">All extracted requirements have supporting evidence.</p>}
    </section>
    <section className="card"><div className="card-head"><h2>Resume text changes</h2></div>
      {baseText && revisedText ? <Changes original={baseText} revised={revisedText} /> : <p className="muted">Text changes are available in the browser tab where both versions were edited.</p>}
    </section>
  </>
}


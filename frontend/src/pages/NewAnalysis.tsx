import { useRef, useState, type FormEvent } from 'react'
import { BriefcaseBusiness, FileText, FlaskConical, LockKeyhole, ScanLine, UploadCloud, X } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { z } from 'zod'
import { api, errorMessage, hostedDemo } from '../api'
import { Feedback, PageHeading } from '../components'
import { demos } from '../demos'
import { getResumes, setContext } from '../storage'

const jobSchema = z.object({
  title: z.string().trim().min(2, 'Enter a job title.'), company: z.string().trim().max(120),
  description: z.string().trim().min(25, 'Paste a job description with at least 25 characters.').max(24000),
})
const resumeSchema = z.string().trim().min(30, 'Paste at least 30 characters of resume text or upload a file.').max(60000)

export function NewAnalysis() {
  const [params] = useSearchParams()
  const demoIndex = params.has('demo') ? Number(params.get('demo')) : -1
  const initialDemo = demos[demoIndex]
  const saved = getResumes().find(item => item.id === params.get('saved'))
  const navigate = useNavigate()
  const input = useRef<HTMLInputElement>(null)
  const [title, setTitle] = useState(initialDemo?.title ?? '')
  const [company, setCompany] = useState(initialDemo?.company ?? '')
  const [description, setDescription] = useState(initialDemo?.description ?? '')
  const [resume, setResume] = useState(saved?.text ?? initialDemo?.resume ?? '')
  const [mode, setMode] = useState<'upload' | 'text'>(saved || initialDemo ? 'text' : 'upload')
  const [sample, setSample] = useState(String(initialDemo ? demoIndex : ''))
  const [file, setFile] = useState<File>()
  const [stage, setStage] = useState('')
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)

  function chooseFile(candidate?: File) {
    setError('')
    if (!candidate) return
    if (!/\.(pdf|docx)$/i.test(candidate.name) || candidate.size > 5 * 1024 * 1024 || !candidate.size) {
      if (input.current) input.current.value = ''
      setError('Choose a non-empty PDF or DOCX file up to 5 MB.')
      return
    }
    setFile(candidate)
  }

  function chooseDemo(value: string) {
    setSample(value)
    const demo = value === '' ? undefined : demos[Number(value)]
    if (!demo) return
    setMode('text')
    setTitle(demo.title)
    setCompany(demo.company)
    setDescription(demo.description)
    setResume(demo.resume)
    setError('')
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (stage) return
    setError('')
    try {
      const job = jobSchema.parse({ title, company, description })
      if (mode === 'upload' && !file) throw new Error('Choose a resume file or switch to Paste text.')
      setStage(mode === 'upload' ? 'Extracting selectable text from your document…' : 'Checking resume text and sections…')
      const parsed = mode === 'upload' && file ? await api.upload(file) : await api.parse(resumeSchema.parse(resume))
      setStage('Extracting job requirements…')
      await api.job(job.description)
      setStage('Running MiniLM embeddings and checking evidence. The first analysis may take longer…')
      const report = await api.analyze({
        ...job, resume: parsed.text, source: parsed.source, warnings: parsed.warnings,
        version: saved?.name ?? (mode === 'upload' ? 'Uploaded ' + parsed.source : sample !== '' ? 'Fictional demo resume' : 'Original resume'),
      })
      const stored = setContext(report.id, { resume: parsed.text, description: job.description })
      navigate('/analysis/' + report.id, { state: stored ? null : { contextUnavailable: true } })
    } catch (reason) {
      setError(reason instanceof z.ZodError ? reason.issues[0].message : errorMessage(reason))
    } finally { setStage('') }
  }

  return <>
    <PageHeading title="New Resume Analysis" description="Compare your resume with a specific role and see which qualifications you can demonstrate.">
      <label className="demo-select"><FlaskConical size={17} /><select aria-label="Try a fictional demo" value={sample} onChange={event => chooseDemo(event.target.value)} disabled={!!stage}>
        <option value="">Try a fictional demo</option>{demos.map((demo, index) => <option key={demo.title} value={index}>{demo.title}</option>)}
      </select></label>
    </PageHeading>
    <form onSubmit={submit} noValidate>
      <fieldset disabled={!!stage} className="form-layout">
        <section className="card form-card"><div className="card-head"><div><h2><FileText size={21} /> Your resume</h2><p>Upload a document or paste your resume text.</p></div></div>
          <div className="tabs" aria-label="Resume input method">
            <button type="button" aria-pressed={mode === 'upload'} onClick={() => setMode('upload')}>Upload file</button>
            <button type="button" aria-pressed={mode === 'text'} onClick={() => setMode('text')}>Paste text</button>
          </div>
          {mode === 'upload' ? <>
            <input ref={input} className="sr-only" type="file" accept=".pdf,.docx" aria-label="Resume file" onChange={event => chooseFile(event.target.files?.[0])} />
            <button type="button" className={'dropzone ' + (dragging ? 'dragging' : '')} onClick={() => input.current?.click()}
              onDragOver={event => { event.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={event => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files[0]) }}>
              <span className="icon-tile"><UploadCloud size={25} /></span>
              <strong>{file ? 'Replace resume file' : 'Click to upload or drag and drop'}</strong><small>PDF or DOCX up to 5 MB</small>
            </button>
            {file && <div className="list-row compact"><FileText size={17} /><strong className="grow file-name">{file.name}</strong>
              <button type="button" className="icon-button" aria-label="Remove file" onClick={() => { setFile(undefined); if (input.current) input.current.value = '' }}><X size={17} /></button></div>}
          </> : <label>Resume text<textarea rows={13} value={resume} maxLength={60000} onChange={event => setResume(event.target.value)} placeholder="Paste your resume, including its section headings." /></label>}
          <div className="form-note"><LockKeyhole size={16} /> {hostedDemo ? 'Use fictional data in this shared demo.' : 'Your document is processed locally.'}</div>
        </section>
        <section className="card form-card"><div className="card-head"><div><h2><BriefcaseBusiness size={21} /> Target job description</h2><p>Include responsibilities and qualifications from the posting.</p></div></div>
          <div className="two"><label>Job title<input required maxLength={120} value={title} onChange={event => setTitle(event.target.value)} placeholder="e.g. Machine Learning Engineer Intern" /></label>
            <label>Company <small>optional</small><input maxLength={120} value={company} onChange={event => setCompany(event.target.value)} placeholder="e.g. Northstar Labs" /></label></div>
          <label>Job description<textarea required rows={11} maxLength={24000} value={description} onChange={event => setDescription(event.target.value)} placeholder={'Paste the role requirements and responsibilities here.'} /></label>
          <small className="count">{description.length.toLocaleString()} / 24,000</small>
        </section>
      </fieldset>
      <div className="form-submit card"><div><ScanLine size={21} /><p>See supported qualifications, evidence gaps, and document readability checks.</p></div>
        <button className="button primary" type="submit" disabled={!!stage}>Analyze Resume Match</button>
      </div>
      <Feedback error={error} busy={stage} />
    </form>
  </>
}


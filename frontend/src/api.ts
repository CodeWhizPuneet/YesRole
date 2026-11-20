import type { Analysis, AnalyzeInput, Parsed, Requirement, Suggestion, Summary } from './types'

const base = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')
export const hostedDemo = import.meta.env.VITE_HOSTED_DEMO === 'true'

// --- Credential management ---
const STORAGE_KEY = 'yesrole_auth'
let _credentials: string | null = sessionStorage.getItem(STORAGE_KEY)

export function setCredentials(username: string, password: string) {
  _credentials = btoa(`${username}:${password}`)
  sessionStorage.setItem(STORAGE_KEY, _credentials)
}

export function clearCredentials() {
  _credentials = null
  sessionStorage.removeItem(STORAGE_KEY)
}

export function hasCredentials(): boolean {
  return _credentials !== null
}

async function request(path: string, init?: RequestInit) {
  const extraHeaders: Record<string, string> = {}
  if (_credentials) extraHeaders['Authorization'] = `Basic ${_credentials}`
  let response: Response
  try {
    response = await fetch(base + '/api' + path, {
      ...init,
      headers: { ...(init?.headers as Record<string, string>), ...extraHeaders },
    })
  } catch {
    throw new Error('Could not reach the local YesRole API. Check that the backend is running.')
  }
  if (response.status === 401) {
    clearCredentials()
    window.dispatchEvent(new Event('yesrole:unauthorized'))
    throw new Error('Session expired. Please sign in again.')
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail || (response.status >= 500
      ? 'The local YesRole API is unavailable. Check that the backend is running.'
      : 'The request could not be completed.'))
  }
  return response
}
const json = <T>(path: string, body?: unknown): Promise<T> => request(path, body === undefined ? undefined : {
  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
}).then(response => response.json())

export const api = {
  upload(file: File) {
    const body = new FormData()
    body.append('file', file)
    return request('/resume/parse', { method: 'POST', body }).then(response => response.json() as Promise<Parsed>)
  },
  parse: (resume: string) => json<Parsed>('/resume/parse-text', { resume }),
  job: (description: string) => json<Requirement[]>('/job/analyze', { description }),
  analyze: (input: AnalyzeInput) => json<Analysis>('/match', input),
  history: () => json<Summary[]>('/analyses'),
  report: (id: string) => json<Analysis>('/analyses/' + encodeURIComponent(id)),
  remove: (id: string) => request('/analyses/' + encodeURIComponent(id), { method: 'DELETE' }),
  capabilities: () => json<{ local_editor: boolean }>('/capabilities'),
  prioritize: (id: string) => json<Suggestion[]>('/resume/optimize/' + encodeURIComponent(id), {}),
  reanalyze: (original_id: string, resume: string, description: string, version: string) =>
    json<Analysis>('/resume/reanalyze', { original_id, resume, description, version }),
  export: (resume: string, format: 'docx' | 'pdf') => request('/resume/export', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ resume, format }),
  }).then(response => response.blob()),
}

export function download(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = name
  anchor.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export async function downloadResume(resume: string, format: 'docx' | 'pdf') {
  download(await api.export(resume, format), 'yesrole-resume.' + format)
}

export const errorMessage = (error: unknown) => error instanceof Error ? error.message : 'Something went wrong. Try again.'


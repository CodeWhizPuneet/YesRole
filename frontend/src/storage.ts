import type { Context, SavedResume } from './types'

const resumeKey = 'yesrole.resumes.v1'
const contextPrefix = 'yesrole.context.'
const dateFormat = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' })
export const displayDate = (date: string) => dateFormat.format(new Date(date))

function read<T>(storage: Storage, key: string, fallback: T): T {
  try {
    const raw = storage.getItem(key)
    return raw ? JSON.parse(raw) as T : fallback
  } catch { return fallback }
}
export const getContext = (id: string) => read<Context | null>(sessionStorage, contextPrefix + id, null)
export function setContext(id: string, value: Context) {
  try {
    sessionStorage.setItem(contextPrefix + id, JSON.stringify(value))
    return true
  } catch { return false }
}
export const getResumes = () => read<SavedResume[]>(localStorage, resumeKey, [])
export const writeResumes = (resumes: SavedResume[]) => localStorage.setItem(resumeKey, JSON.stringify(resumes))
export function saveResume(name: string, text: string, id?: string) {
  const resume = { id: id ?? crypto.randomUUID(), name, text, updatedAt: new Date().toISOString() }
  writeResumes([resume, ...getResumes().filter(existing => existing.id !== resume.id)])
  return resume
}
export function forgetContext(id: string) {
  sessionStorage.removeItem(contextPrefix + id)
}
export function clearBrowserData() {
  writeResumes([])
  for (const key of Object.keys(sessionStorage)) {
    if (key.startsWith(contextPrefix)) sessionStorage.removeItem(key)
  }
}


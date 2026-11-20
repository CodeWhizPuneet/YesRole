export const statuses = ['Supported', 'Partially Supported', 'Not Evidenced'] as const
export type Status = (typeof statuses)[number]
export type Source = 'PDF' | 'DOCX' | 'Text'
export type Parsed = {
  text: string
  sections: { title: string; text: string }[]
  source: Source
  warnings: string[]
}
export type Requirement = {
  id: string; text: string; category: string; priority: 'Required' | 'Preferred'; skills: string[]; weight: number
}
export type Finding = {
  requirement: Requirement; status: Status
  evidence: { section: string; text: string; similarity: number } | null
  additional_evidence?: { section: string; text: string; similarity: number }[]
  explanation: string
}
export type Check = { name: string; status: 'Pass' | 'Issue' | 'Warning'; detail: string }
export type Suggestion = {
  id: string; kind: 'Safe Rephrasing' | 'Needs User Confirmation'; title: string; detail: string
  original: string | null; replacement: string | null
}
export type Analysis = {
  id: string; created_at: string; title: string; company: string; version: string; score: number
  dimensions: { name: string; value: number; weight: number }[]
  findings: Finding[]; ats: Check[]; suggestions: Suggestion[]; model: string; parent_id: string | null
}
export type Summary = Pick<Analysis, 'id' | 'created_at' | 'title' | 'company' | 'score' | 'version' | 'parent_id'> & {
  supported: number; total: number; change: number | null
}
export type Context = { resume: string; description: string }
export type SavedResume = { id: string; name: string; text: string; updatedAt: string }
export type AnalyzeInput = Context & { title: string; company: string; version: string; source: Source; warnings: string[] }


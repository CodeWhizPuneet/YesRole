import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { App } from './App'
import type { Analysis } from './types'

const example: Analysis = {
  id: 'one', created_at: '2026-11-20T10:00:00Z', title: 'ML Intern', company: 'Northstar Labs',
  version: 'Original resume', score: 42, parent_id: null, model: 'sentence-transformers/all-MiniLM-L6-v2',
  dimensions: [{ name: 'Semantic relevance', value: 39, weight: 20 }],
  findings: [{
    requirement: { id: 'R01', text: 'Docker experience', category: 'Technical skills', priority: 'Required', skills: ['Docker'], weight: 1 },
    status: 'Not Evidenced', evidence: { section: 'Projects', text: 'Built a Python classifier.', similarity: .35 },
    explanation: 'Docker is not named in this resume.',
  }],
  ats: [{ name: 'Contact information', status: 'Warning', detail: 'Could not identify a phone number.' }],
  suggestions: [],
}
beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn((url: string) => Promise.resolve(new Response(JSON.stringify(url.endsWith('/one') ? example : []), {
    headers: { 'Content-Type': 'application/json' },
  }))))
})
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

test('dashboard navigation opens the analysis form and fictional demo', async () => {
  render(<MemoryRouter><App /></MemoryRouter>)
  expect(await screen.findByText('No analyses yet')).toBeTruthy()
  fireEvent.click(screen.getByRole('link', { name: 'Try Demo' }))
  expect(screen.getByRole('heading', { name: 'New Resume Analysis' })).toBeTruthy()
  expect((screen.getByRole('textbox', { name: 'Job title' }) as HTMLInputElement).value).toBe('Machine Learning Engineer Intern')
  expect(screen.getByRole('button', { name: 'Analyze Resume Match' })).toBeTruthy()
})

test('report displays exact evidence and makes gaps independently filterable', async () => {
  render(<MemoryRouter initialEntries={['/analysis/one']}><App /></MemoryRouter>)
  expect(await screen.findByText('YesRole Match Score')).toBeTruthy()
  expect(screen.getByText('42')).toBeTruthy()
  fireEvent.click(screen.getByText('Docker experience'))
  expect(screen.getByText('Built a Python classifier.')).toBeTruthy()
  fireEvent.change(screen.getByRole('combobox', { name: 'Filter by classification' }), { target: { value: 'Supported' } })
  expect(screen.queryByText('Docker experience')).toBeNull()
  expect(screen.getByText('No requirements in this category')).toBeTruthy()
  expect(screen.getByText('ATS Readability')).toBeTruthy()
})


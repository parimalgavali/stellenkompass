import { beforeEach, describe, expect, it, vi } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'
import { JOBS } from './test/data'

beforeEach(() => {
  window.location.hash = ''
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (url.endsWith('jobs.json')) {
        return new Response(JSON.stringify({ generated_at: '2026-11-03T05:00:00Z', count: JOBS.length, jobs: JOBS }))
      }
      return new Response(
        JSON.stringify({ generated_at: '', total_jobs: 3, sources: { greenhouse: { boards: 1, jobs: 1, errors: [], seconds: 1 } } }),
      )
    }),
  )
})

describe('App', () => {
  it('lists, searches and saves roles into the tracker', async () => {
    const user = userEvent.setup()
    render(<App />)
    expect(await screen.findByText('3 roles')).toBeInTheDocument()
    expect(screen.getByText(/greenhouse 1/)).toBeInTheDocument()

    await user.type(screen.getByLabelText('Search'), 'frontend')
    expect(screen.getByText('1 roles')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Save Frontend Developer' }))
    expect(screen.getByRole('button', { name: 'In tracker: Saved' })).toBeDisabled()
    expect(JSON.parse(localStorage.getItem('stellenkompass.tracker')!)).toHaveProperty(['lever:y-3'])

    await user.click(screen.getByRole('link', { name: /Tracker/ }))
    const card = (await screen.findByRole('link', { name: 'Frontend Developer' })).closest('article')!
    await user.selectOptions(within(card).getByDisplayValue('Saved'), 'applied')
    expect(within(card).getByLabelText('Applied')).not.toHaveValue('')
  })

  it('adds keywords and filters to matches', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('3 roles')
    await user.click(screen.getByRole('link', { name: 'Profile' }))
    await user.type(screen.getByLabelText('Add keywords'), 'machine learning{Enter}')
    expect(screen.getByRole('button', { name: 'Remove machine learning' })).toBeInTheDocument()

    await user.click(screen.getByRole('link', { name: 'Jobs' }))
    await user.click(screen.getByLabelText('My matches'))
    expect(screen.getByText('1 roles')).toBeInTheDocument()
    expect(screen.getByText('machine learning', { selector: '.chip' })).toBeInTheDocument()
  })

  it('imports a backup file', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('3 roles')
    await user.click(screen.getByRole('link', { name: 'Profile' }))
    const backup = { app: 'stellenkompass', version: 1, exportedAt: '', profile: { keywords: ['rust'], companies: [] }, tracker: {} }
    const file = new File([JSON.stringify(backup)], 'b.json', { type: 'application/json' })
    await user.upload(screen.getByTestId('import-file'), file)
    expect(await screen.findByText(/Imported 0 tracked roles/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Remove rust' })).toBeInTheDocument()
  })

  it('reads skills from a CV and sorts by fit', async () => {
    const user = userEvent.setup()
    render(<App />)
    await screen.findByText('3 roles')
    await user.click(screen.getByRole('link', { name: 'Profile' }))
    const cv = new File(['Data engineer: Python, SQL and Docker. Maschinelles Lernen.'], 'cv.txt', { type: 'text/plain' })
    await user.upload(screen.getByTestId('cv-file'), cv)
    expect(await screen.findByText(/Found 4 skills in cv.txt/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Remove Docker' })).toBeInTheDocument()
    expect(JSON.parse(localStorage.getItem('stellenkompass.profile')!).skills).toEqual(['Python', 'SQL', 'Machine Learning', 'Docker'])

    await user.click(screen.getByRole('link', { name: 'Jobs' }))
    await user.selectOptions(screen.getByLabelText('Sort'), 'fit')
    expect(screen.getAllByText(/^Fit \d+%$/).map((el) => el.textContent)).toEqual(['Fit 100%', 'Fit 67%', 'Fit 0%'])
  })
})

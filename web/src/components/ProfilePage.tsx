import { useRef, useState } from 'react'
import type { Profile, Tracker } from '../types'
import { makeBackup, mergeBackup, parseBackup } from '../lib/backup'

interface Props {
  profile: Profile
  tracker: Tracker
  onProfile: (p: Profile) => void
  onRestore: (p: Profile, t: Tracker) => void
}

function ListEditor({ label, hint, items, onChange }: { label: string; hint: string; items: string[]; onChange: (v: string[]) => void }) {
  const [draft, setDraft] = useState('')
  const add = () => {
    const values = draft.split(',').map((v) => v.trim()).filter(Boolean)
    const fresh = values.filter((v) => !items.some((i) => i.toLowerCase() === v.toLowerCase()))
    if (fresh.length) onChange([...items, ...fresh])
    setDraft('')
  }
  return (
    <div className="editor">
      <h3>{label}</h3>
      <p className="hint">{hint}</p>
      <form
        className="add-row"
        onSubmit={(e) => {
          e.preventDefault()
          add()
        }}
      >
        <input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Type and press Enter" aria-label={`Add ${label.toLowerCase()}`} />
        <button className="btn" type="submit">Add</button>
      </form>
      <div className="chips">
        {items.map((item) => (
          <span key={item} className="chip chip-removable">
            {item}
            <button onClick={() => onChange(items.filter((i) => i !== item))} aria-label={`Remove ${item}`}>
              ×
            </button>
          </span>
        ))}
      </div>
    </div>
  )
}

export function ProfilePage({ profile, tracker, onProfile, onRestore }: Props) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [mode, setMode] = useState<'merge' | 'replace'>('merge')
  const [status, setStatus] = useState<{ ok: boolean; text: string } | null>(null)

  const exportFile = () => {
    const blob = new Blob([JSON.stringify(makeBackup(profile, tracker), null, 2)], { type: 'application/json' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = `stellenkompass-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  const importFile = async (file: File) => {
    try {
      const backup = parseBackup(await file.text())
      const roles = Object.keys(backup.tracker).length
      if (mode === 'replace') {
        if (!window.confirm('Replace your keywords, companies and tracker with this file? This cannot be undone.')) return
        onRestore(backup.profile, backup.tracker)
      } else {
        const merged = mergeBackup(profile, tracker, backup)
        onRestore(merged.profile, merged.tracker)
      }
      setStatus({ ok: true, text: `Imported ${roles} tracked roles (${mode}).` })
    } catch (err) {
      setStatus({ ok: false, text: (err as Error).message })
    } finally {
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  return (
    <section>
      <ListEditor
        label="Keywords"
        hint="Roles whose title or tags contain one of these are your matches. Separate several with commas."
        items={profile.keywords}
        onChange={(keywords) => onProfile({ ...profile, keywords })}
      />
      <ListEditor
        label="Followed companies"
        hint="Every open role at these companies counts as a match."
        items={profile.companies}
        onChange={(companies) => onProfile({ ...profile, companies })}
      />
      <div className="editor">
        <h3>Backup</h3>
        <p className="hint">Your profile and tracker live only in this browser. Export them to keep a copy or move to another device.</p>
        <div className="add-row">
          <button className="btn" onClick={exportFile}>Export JSON</button>
          <select value={mode} onChange={(e) => setMode(e.target.value as 'merge' | 'replace')} aria-label="Import mode">
            <option value="merge">Import: merge</option>
            <option value="replace">Import: replace</option>
          </select>
          <button className="btn btn-quiet" onClick={() => fileRef.current?.click()}>Choose file…</button>
          <input
            ref={fileRef}
            type="file"
            accept="application/json,.json"
            hidden
            data-testid="import-file"
            onChange={(e) => e.target.files?.[0] && importFile(e.target.files[0])}
          />
        </div>
        {status && <p className={status.ok ? 'notice' : 'notice notice-error'}>{status.text}</p>}
      </div>
    </section>
  )
}

import { useCallback, useState, DragEvent, ChangeEvent } from 'react'

interface Props {
  onFile: (file: File) => void
}

export default function UploadSection({ onFile }: Props) {
  const [dragging, setDragging] = useState(false)
  const [error, setError] = useState('')

  const validate = (file: File): string => {
    if (!file.name.toLowerCase().endsWith('.pdf')) return 'Only PDF files are supported.'
    if (file.size > 10 * 1024 * 1024) return 'File must be under 10 MB.'
    if (file.size === 0) return 'File appears to be empty.'
    return ''
  }

  const process = useCallback((file: File) => {
    const err = validate(file)
    if (err) { setError(err); return }
    setError('')
    onFile(file)
  }, [onFile])

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) process(file)
  }

  const onChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) process(file)
  }

  return (
    <div style={{ maxWidth: 760, margin: '0 auto' }}>
      {/* Hero */}
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: '#dbeafe', color: '#1d4ed8',
          padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
          marginBottom: 20, letterSpacing: '0.4px',
        }}>
          TRUTH LAYER · AI FACT-CHECKING
        </div>
        <h1 style={{ fontSize: 36, fontWeight: 800, lineHeight: 1.2, color: '#0f172a', marginBottom: 16, letterSpacing: '-0.5px' }}>
          Verify every claim in your document
        </h1>
        <p style={{ fontSize: 16, color: '#475569', maxWidth: 520, margin: '0 auto', lineHeight: 1.65 }}>
          Upload a PDF and our AI instantly extracts statistics, dates, financial figures
          and technical claims — then cross-references each one against live web sources.
        </p>
      </div>

      {/* Upload Zone */}
      <label htmlFor="pdf-input" style={{ display: 'block', cursor: 'pointer' }}>
        <div
          onDragOver={e => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          style={{
            border: `2px dashed ${dragging ? '#0f62fe' : '#cbd5e1'}`,
            borderRadius: 16,
            background: dragging ? '#eff6ff' : '#fff',
            padding: '56px 32px',
            textAlign: 'center',
            transition: 'all 0.2s ease',
            boxShadow: dragging ? '0 0 0 4px rgba(15,98,254,0.10)' : '0 1px 4px rgba(0,0,0,0.06)',
          }}
        >
          <div style={{ fontSize: 52, marginBottom: 20 }}>📄</div>
          <div style={{ fontWeight: 700, fontSize: 18, color: '#1e293b', marginBottom: 8 }}>
            {dragging ? 'Drop your PDF here' : 'Drag & drop your PDF'}
          </div>
          <div style={{ color: '#64748b', fontSize: 14, marginBottom: 24 }}>
            or click to browse files
          </div>
          <div style={{
            display: 'inline-block',
            background: '#0f62fe', color: '#fff',
            padding: '11px 28px', borderRadius: 8,
            fontWeight: 600, fontSize: 14,
            boxShadow: '0 2px 6px rgba(15,98,254,0.35)',
          }}>
            Select PDF File
          </div>
          <div style={{ marginTop: 20, color: '#94a3b8', fontSize: 12 }}>
            PDF only · Max 10 MB · Text-based (not scanned images)
          </div>
        </div>
      </label>
      <input
        id="pdf-input"
        type="file"
        accept="application/pdf"
        onChange={onChange}
        style={{ display: 'none' }}
      />

      {error && (
        <div style={{
          marginTop: 16, padding: '12px 16px',
          background: '#fee2e2', border: '1px solid #fecaca',
          borderRadius: 8, color: '#b91c1c', fontSize: 13, fontWeight: 500,
        }}>
          {error}
        </div>
      )}

      {/* Feature cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16, marginTop: 40 }}>
        {[
          { icon: '🔍', title: 'Smart Extraction', desc: 'Detects stats, dates, financial figures, percentages and technical claims using pattern matching + NLP.' },
          { icon: '🌐', title: 'Live Verification', desc: 'Cross-references every claim against current web sources using Tavily AI search in real time.' },
          { icon: '📊', title: 'Confidence Scoring', desc: 'Each claim receives a 0-100% confidence score with supporting evidence and source links.' },
        ].map(f => (
          <div key={f.title} style={{
            background: '#fff', border: '1px solid #e5e7eb',
            borderRadius: 12, padding: '20px 18px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
          }}>
            <div style={{ fontSize: 28, marginBottom: 12 }}>{f.icon}</div>
            <div style={{ fontWeight: 700, fontSize: 14, color: '#1e293b', marginBottom: 6 }}>{f.title}</div>
            <div style={{ fontSize: 12, color: '#64748b', lineHeight: 1.55 }}>{f.desc}</div>
          </div>
        ))}
      </div>

      {/* Category legend */}
      <div style={{
        marginTop: 32, padding: '18px 22px',
        background: '#f8fafc', border: '1px solid #e2e8f0',
        borderRadius: 12,
      }}>
        <div style={{ fontWeight: 600, fontSize: 13, color: '#334155', marginBottom: 12 }}>Verification Categories</div>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          {[
            { color: '#15803d', bg: '#dcfce7', label: 'Verified', desc: 'Supported by sources' },
            { color: '#b45309', bg: '#fef9c3', label: 'Inaccurate', desc: 'Contains errors / outdated' },
            { color: '#b91c1c', bg: '#fee2e2', label: 'False', desc: 'Contradicted by sources' },
            { color: '#6b7280', bg: '#f3f4f6', label: 'Unverifiable', desc: 'Insufficient evidence' },
          ].map(c => (
            <div key={c.label} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{
                background: c.bg, color: c.color,
                padding: '2px 10px', borderRadius: 20,
                fontSize: 12, fontWeight: 700,
              }}>{c.label}</span>
              <span style={{ fontSize: 12, color: '#64748b' }}>{c.desc}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

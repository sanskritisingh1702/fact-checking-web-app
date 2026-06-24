import { useState } from 'react'
import { VerificationResult, ClaimCategory, SortKey, SortDir } from '../types'

interface Props {
  results: VerificationResult[]
  docName: string
  sessionId: string | null
  onReset: () => void
}

const CATEGORY_STYLES: Record<ClaimCategory, { bg: string; color: string; border: string }> = {
  Verified:      { bg: '#dcfce7', color: '#15803d', border: '#bbf7d0' },
  Inaccurate:    { bg: '#fef9c3', color: '#b45309', border: '#fde68a' },
  False:         { bg: '#fee2e2', color: '#b91c1c', border: '#fecaca' },
  Unverifiable:  { bg: '#f3f4f6', color: '#6b7280', border: '#d1d5db' },
}

const CATEGORY_ICON: Record<ClaimCategory, string> = {
  Verified: '✓', Inaccurate: '!', False: '✗', Unverifiable: '?'
}

export default function ResultsView({ results, docName, onReset }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>('confidence_score')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [filterCategory, setFilterCategory] = useState<ClaimCategory | 'All'>('All')
  const [expanded, setExpanded] = useState<number | null>(null)
  const [search, setSearch] = useState('')

  const verified    = results.filter(r => r.category === 'Verified').length
  const inaccurate  = results.filter(r => r.category === 'Inaccurate').length
  const falseCount  = results.filter(r => r.category === 'False').length
  const unverifiable = results.filter(r => r.category === 'Unverifiable').length
  const avgConf     = results.reduce((s, r) => s + r.confidence_score, 0) / (results.length || 1)

  const handleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const displayed = [...results]
    .filter(r => filterCategory === 'All' || r.category === filterCategory)
    .filter(r => !search || r.claim_text.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      let av: number | string, bv: number | string
      if (sortKey === 'confidence_score') { av = a.confidence_score; bv = b.confidence_score }
      else if (sortKey === 'category') { av = a.category; bv = b.category }
      else { av = a.page_number; bv = b.page_number }
      if (av < bv) return sortDir === 'asc' ? -1 : 1
      if (av > bv) return sortDir === 'asc' ? 1 : -1
      return 0
    })

  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
    a.download = `fact-check-${Date.now()}.json`; a.click()
  }

  const downloadCSV = () => {
    const header = 'Claim,Type,Category,Confidence,Page,Explanation,Sources'
    const rows = results.map(r =>
      [
        `"${r.claim_text.replace(/"/g, '""')}"`,
        r.claim_type, r.category, `${r.confidence_score}%`, r.page_number,
        `"${r.explanation.replace(/"/g, '""')}"`,
        `"${r.source_urls.slice(0,3).join('; ')}"`
      ].join(',')
    )
    const blob = new Blob([[header, ...rows].join('\n')], { type: 'text/csv' })
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob)
    a.download = `fact-check-${Date.now()}.csv`; a.click()
  }

  const SortBtn = ({ k, label }: { k: SortKey; label: string }) => (
    <button
      onClick={() => handleSort(k)}
      style={{
        background: 'none', border: 'none', cursor: 'pointer',
        fontWeight: 600, fontSize: 12, color: sortKey === k ? '#0f62fe' : '#64748b',
        display: 'flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap',
        padding: 0,
      }}
    >
      {label}
      <span style={{ fontSize: 10, opacity: sortKey === k ? 1 : 0.4 }}>
        {sortKey === k ? (sortDir === 'desc' ? '▼' : '▲') : '⇅'}
      </span>
    </button>
  )

  return (
    <div style={{ maxWidth: 1060, margin: '0 auto' }}>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, marginBottom: 28, flexWrap: 'wrap' }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 800, color: '#0f172a', marginBottom: 4 }}>Verification Results</h2>
          <p style={{ color: '#64748b', fontSize: 13 }}>
            {results.length} claims extracted from <strong>{docName}</strong>
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button onClick={downloadCSV} style={{
            background: '#fff', border: '1px solid #d1d5db', borderRadius: 8,
            padding: '9px 18px', fontWeight: 600, fontSize: 13, color: '#374151',
            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
          }}>
            ↓ CSV
          </button>
          <button onClick={downloadJSON} style={{
            background: '#fff', border: '1px solid #d1d5db', borderRadius: 8,
            padding: '9px 18px', fontWeight: 600, fontSize: 13, color: '#374151',
            cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
          }}>
            ↓ JSON
          </button>
          <button onClick={onReset} style={{
            background: '#0f62fe', color: '#fff', border: 'none', borderRadius: 8,
            padding: '9px 20px', fontWeight: 600, fontSize: 13, cursor: 'pointer',
          }}>
            + New Document
          </button>
        </div>
      </div>

      {/* Summary metrics */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 28 }}>
        {[
          { label: 'Total Claims', value: results.length, color: '#1e293b', bg: '#f8fafc', border: '#e2e8f0' },
          { label: 'Verified', value: verified, color: '#15803d', bg: '#dcfce7', border: '#bbf7d0' },
          { label: 'Inaccurate', value: inaccurate, color: '#b45309', bg: '#fef9c3', border: '#fde68a' },
          { label: 'False', value: falseCount, color: '#b91c1c', bg: '#fee2e2', border: '#fecaca' },
          { label: 'Avg Confidence', value: `${avgConf.toFixed(1)}%`, color: '#1d4ed8', bg: '#eff6ff', border: '#bfdbfe' },
        ].map(m => (
          <div key={m.label} style={{
            background: m.bg, border: `1px solid ${m.border}`,
            borderRadius: 12, padding: '16px 14px', textAlign: 'center',
          }}>
            <div style={{ fontSize: 24, fontWeight: 800, color: m.color, lineHeight: 1 }}>{m.value}</div>
            <div style={{ fontSize: 11, color: '#64748b', marginTop: 5, fontWeight: 500 }}>{m.label}</div>
          </div>
        ))}
      </div>

      {/* Category bar */}
      {results.length > 0 && (
        <div style={{ height: 10, borderRadius: 99, overflow: 'hidden', display: 'flex', marginBottom: 28 }}>
          {[
            { cat: 'Verified', count: verified, color: '#22c55e' },
            { cat: 'Inaccurate', count: inaccurate, color: '#eab308' },
            { cat: 'False', count: falseCount, color: '#ef4444' },
            { cat: 'Unverifiable', count: unverifiable, color: '#9ca3af' },
          ].filter(s => s.count > 0).map(s => (
            <div
              key={s.cat}
              title={`${s.cat}: ${s.count}`}
              style={{ width: `${(s.count / results.length) * 100}%`, background: s.color }}
            />
          ))}
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {(['All', 'Verified', 'Inaccurate', 'False', 'Unverifiable'] as const).map(cat => {
            const active = filterCategory === cat
            const style = cat !== 'All' ? CATEGORY_STYLES[cat as ClaimCategory] : null
            return (
              <button
                key={cat}
                onClick={() => setFilterCategory(cat)}
                style={{
                  padding: '6px 14px', borderRadius: 20, fontSize: 12, fontWeight: 600,
                  cursor: 'pointer', border: '1.5px solid',
                  borderColor: active ? (style?.border ?? '#0f62fe') : '#d1d5db',
                  background: active ? (style?.bg ?? '#eff6ff') : '#fff',
                  color: active ? (style?.color ?? '#0f62fe') : '#6b7280',
                  transition: 'all 0.15s',
                }}
              >
                {cat} {cat !== 'All' && cat === 'Verified' && `(${verified})`}
                {cat === 'Inaccurate' && `(${inaccurate})`}
                {cat === 'False' && `(${falseCount})`}
                {cat === 'Unverifiable' && `(${unverifiable})`}
              </button>
            )
          })}
        </div>
        <input
          placeholder="Search claims…"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            marginLeft: 'auto', padding: '6px 12px', border: '1.5px solid #d1d5db',
            borderRadius: 8, fontSize: 13, outline: 'none', minWidth: 180,
            color: '#374151',
          }}
        />
      </div>

      {/* Table */}
      <div style={{
        background: '#fff', border: '1px solid #e5e7eb',
        borderRadius: 12, overflow: 'hidden',
        boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
      }}>
        {/* Table header */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '2fr 1fr 120px 100px 48px',
          gap: 0,
          background: '#f8fafc',
          borderBottom: '1px solid #e5e7eb',
          padding: '10px 16px',
        }}>
          <span style={{ fontWeight: 600, fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Claim</span>
          <span style={{ fontWeight: 600, fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Type</span>
          <SortBtn k="category" label="Status" />
          <SortBtn k="confidence_score" label="Confidence" />
          <SortBtn k="page_number" label="Pg" />
        </div>

        {/* Rows */}
        {displayed.length === 0 ? (
          <div style={{ padding: '48px 16px', textAlign: 'center', color: '#94a3b8', fontSize: 14 }}>
            No claims match the current filter.
          </div>
        ) : (
          displayed.map((result, i) => {
            const styles = CATEGORY_STYLES[result.category]
            const isExpanded = expanded === i
            return (
              <div key={i} style={{ borderBottom: i < displayed.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                {/* Row */}
                <div
                  onClick={() => setExpanded(isExpanded ? null : i)}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '2fr 1fr 120px 100px 48px',
                    gap: 0,
                    padding: '14px 16px',
                    cursor: 'pointer',
                    background: isExpanded ? '#f8fafc' : 'transparent',
                    transition: 'background 0.15s',
                    alignItems: 'center',
                  }}
                >
                  {/* Claim text */}
                  <span style={{
                    fontSize: 13, color: '#1e293b', fontWeight: 500,
                    overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis',
                    paddingRight: 12,
                  }} title={result.claim_text}>
                    {result.claim_text}
                  </span>
                  {/* Type */}
                  <span style={{ fontSize: 11, color: '#64748b', paddingRight: 8, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {result.claim_type}
                  </span>
                  {/* Status badge */}
                  <span>
                    <span style={{
                      display: 'inline-flex', alignItems: 'center', gap: 4,
                      background: styles.bg, color: styles.color,
                      border: `1px solid ${styles.border}`,
                      padding: '3px 10px', borderRadius: 20,
                      fontSize: 11, fontWeight: 700,
                    }}>
                      {CATEGORY_ICON[result.category]} {result.category}
                    </span>
                  </span>
                  {/* Confidence */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ flex: 1, height: 5, background: '#e2e8f0', borderRadius: 99, overflow: 'hidden', minWidth: 40 }}>
                        <div style={{
                          width: `${result.confidence_score}%`,
                          height: '100%',
                          background: result.confidence_score > 70 ? '#22c55e' : result.confidence_score > 40 ? '#eab308' : '#ef4444',
                          borderRadius: 99,
                        }} />
                      </div>
                      <span style={{ fontSize: 12, fontWeight: 600, color: '#374151', minWidth: 36 }}>
                        {result.confidence_score.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  {/* Page */}
                  <span style={{ fontSize: 12, color: '#94a3b8', textAlign: 'center' }}>
                    {result.page_number}
                  </span>
                </div>

                {/* Expanded detail panel */}
                {isExpanded && (
                  <div style={{
                    padding: '0 16px 20px',
                    borderTop: '1px solid #f1f5f9',
                    background: '#f8fafc',
                  }}>
                    <div style={{ paddingTop: 16, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                      {/* Left */}
                      <div>
                        <div style={{ marginBottom: 14 }}>
                          <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 6 }}>Full Claim</div>
                          <div style={{ fontSize: 13, color: '#1e293b', lineHeight: 1.55, background: '#fff', padding: '10px 12px', borderRadius: 8, border: '1px solid #e5e7eb' }}>
                            {result.claim_text}
                          </div>
                        </div>

                        <div>
                          <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 6 }}>Explanation</div>
                          <div style={{ fontSize: 13, color: '#475569', lineHeight: 1.6 }}>
                            {result.explanation || 'No explanation available.'}
                          </div>
                        </div>
                      </div>

                      {/* Right */}
                      <div>
                        {result.evidence.length > 0 && (
                          <div style={{ marginBottom: 14 }}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>Supporting Evidence</div>
                            {result.evidence.slice(0, 3).map((ev, j) => (
                              <div key={j} style={{
                                fontSize: 12, color: '#475569', lineHeight: 1.5,
                                padding: '8px 10px', background: '#fff',
                                border: '1px solid #e5e7eb', borderRadius: 6, marginBottom: 6,
                              }}>
                                "{ev.length > 180 ? ev.slice(0, 180) + '…' : ev}"
                              </div>
                            ))}
                          </div>
                        )}

                        {result.source_urls.length > 0 && (
                          <div>
                            <div style={{ fontSize: 11, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>Sources</div>
                            {result.source_urls.slice(0, 3).map((url, j) => (
                              <div key={j} style={{ marginBottom: 4 }}>
                                <a
                                  href={url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  style={{
                                    fontSize: 12, color: '#2563eb',
                                    display: 'block', overflow: 'hidden',
                                    textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                                  }}
                                >
                                  {url}
                                </a>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>

      <div style={{ textAlign: 'center', marginTop: 14, color: '#94a3b8', fontSize: 12 }}>
        Showing {displayed.length} of {results.length} claims
      </div>
    </div>
  )
}

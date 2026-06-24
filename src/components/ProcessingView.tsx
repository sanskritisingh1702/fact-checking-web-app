interface Props {
  progress: number
  label: string
}

const steps = [
  { threshold: 5,  icon: '📤', text: 'Uploading document' },
  { threshold: 20, icon: '📄', text: 'Extracting PDF text' },
  { threshold: 40, icon: '🔍', text: 'Identifying claims' },
  { threshold: 60, icon: '🌐', text: 'Verifying against web' },
  { threshold: 85, icon: '💾', text: 'Saving results' },
  { threshold: 100, icon: '✅', text: 'Complete!' },
]

export default function ProcessingView({ progress, label }: Props) {
  return (
    <div style={{ maxWidth: 560, margin: '60px auto', textAlign: 'center' }}>
      <div style={{ fontSize: 48, marginBottom: 24 }}>
        {progress < 100 ? '⚙️' : '✅'}
      </div>
      <h2 style={{ fontSize: 22, fontWeight: 700, color: '#1e293b', marginBottom: 8 }}>
        {progress < 100 ? 'Analyzing Document' : 'Complete!'}
      </h2>
      <p style={{ color: '#64748b', fontSize: 14, marginBottom: 36, minHeight: 20 }}>
        {label}
      </p>

      {/* Progress bar */}
      <div style={{
        background: '#e2e8f0', borderRadius: 99, height: 10,
        marginBottom: 12, overflow: 'hidden',
      }}>
        <div style={{
          width: `${progress}%`,
          height: '100%',
          background: 'linear-gradient(90deg, #0f62fe, #06b6d4)',
          borderRadius: 99,
          transition: 'width 0.5s ease',
        }} />
      </div>
      <div style={{ color: '#0f62fe', fontWeight: 700, fontSize: 14, marginBottom: 40 }}>
        {progress}%
      </div>

      {/* Step list */}
      <div style={{ textAlign: 'left', display: 'inline-block', minWidth: 280 }}>
        {steps.map((step, i) => {
          const done = progress >= step.threshold
          const active = progress < step.threshold && (i === 0 || progress >= steps[i - 1].threshold)
          return (
            <div key={step.text} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '8px 0',
              borderBottom: i < steps.length - 1 ? '1px solid #f1f5f9' : 'none',
              opacity: done || active ? 1 : 0.35,
              transition: 'opacity 0.3s',
            }}>
              <span style={{ fontSize: 18, minWidth: 28, textAlign: 'center' }}>{step.icon}</span>
              <span style={{
                fontSize: 13,
                fontWeight: active ? 700 : done ? 500 : 400,
                color: done ? '#15803d' : active ? '#0f62fe' : '#64748b',
              }}>
                {step.text}
                {done && !active && <span style={{ marginLeft: 6, color: '#15803d' }}>✓</span>}
              </span>
            </div>
          )
        })}
      </div>

      <div style={{ marginTop: 32, color: '#94a3b8', fontSize: 12 }}>
        This may take 30–90 seconds depending on document size
      </div>
    </div>
  )
}

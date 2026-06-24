import { useState, useCallback } from 'react'
import { supabase, invokeFunction } from './lib/supabase'
import { VerificationResult } from './types'
import UploadSection from './components/UploadSection'
import ProcessingView from './components/ProcessingView'
import ResultsView from './components/ResultsView'

type AppState = 'idle' | 'processing' | 'done' | 'error'

export default function App() {
  const [state, setState] = useState<AppState>('idle')
  const [progress, setProgress] = useState(0)
  const [progressLabel, setProgressLabel] = useState('')
  const [results, setResults] = useState<VerificationResult[]>([])
  const [docName, setDocName] = useState('')
  const [errorMsg, setErrorMsg] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)

  const handleFile = useCallback(async (file: File) => {
    setState('processing')
    setDocName(file.name)
    setProgress(5)
    setProgressLabel('Uploading document…')
    setErrorMsg('')

    try {
      // Step 1: extract text + claims via edge function
      const formData = new FormData()
      formData.append('file', file)

      setProgress(20)
      setProgressLabel('Extracting text from PDF…')

      const extractResult = await invokeFunction<{ claims: Array<{ text: string; claim_type: string; source_text: string; page_number: number }> }>(
        'process-pdf',
        formData
      )

      const claims = extractResult.claims ?? []

      if (claims.length === 0) {
        setErrorMsg('No verifiable claims were found in this document. Make sure the PDF contains selectable text (not a scanned image).')
        setState('error')
        return
      }

      setProgress(45)
      setProgressLabel(`Found ${claims.length} claims — verifying against live web…`)

      // Step 2: verify claims
      const verifyResult = await invokeFunction<{ results: VerificationResult[] }>(
        'verify-claims',
        { claims }
      )

      const verifiedResults = verifyResult.results ?? []
      setProgress(85)
      setProgressLabel('Saving results…')

      // Step 3: persist session to Supabase
      const { data: session } = await supabase
        .from('verification_sessions')
        .insert({
          document_name: file.name,
          total_claims: verifiedResults.length,
          verified_count: verifiedResults.filter(r => r.category === 'Verified').length,
          inaccurate_count: verifiedResults.filter(r => r.category === 'Inaccurate').length,
          false_count: verifiedResults.filter(r => r.category === 'False').length,
          unverifiable_count: verifiedResults.filter(r => r.category === 'Unverifiable').length,
          avg_confidence: verifiedResults.reduce((s, r) => s + r.confidence_score, 0) / (verifiedResults.length || 1),
        })
        .select()
        .single()

      if (session) {
        setSessionId(session.id)
        await supabase.from('verification_claims').insert(
          verifiedResults.map(r => ({
            session_id: session.id,
            claim_text: r.claim_text,
            claim_type: r.claim_type,
            page_number: r.page_number,
            category: r.category,
            confidence_score: r.confidence_score,
            evidence: r.evidence,
            source_urls: r.source_urls,
            explanation: r.explanation,
          }))
        )
      }

      setProgress(100)
      setProgressLabel('Done!')
      setResults(verifiedResults)
      setState('done')
    } catch (err) {
      console.error(err)
      setErrorMsg(err instanceof Error ? err.message : 'An unexpected error occurred.')
      setState('error')
    }
  }, [])

  const reset = () => {
    setState('idle')
    setResults([])
    setDocName('')
    setProgress(0)
    setProgressLabel('')
    setErrorMsg('')
    setSessionId(null)
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header />
      <main style={{ flex: 1, padding: '32px 24px', maxWidth: 1100, margin: '0 auto', width: '100%' }}>
        {state === 'idle' && <UploadSection onFile={handleFile} />}
        {state === 'processing' && <ProcessingView progress={progress} label={progressLabel} />}
        {state === 'error' && (
          <ErrorView message={errorMsg} onRetry={reset} />
        )}
        {state === 'done' && (
          <ResultsView
            results={results}
            docName={docName}
            sessionId={sessionId}
            onReset={reset}
          />
        )}
      </main>
      <Footer />
    </div>
  )
}

function Header() {
  return (
    <header style={{
      background: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%)',
      color: '#fff',
      padding: '0 24px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
    }}>
      <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', alignItems: 'center', gap: 14, padding: '18px 0' }}>
        <div style={{
          width: 40, height: 40, borderRadius: 10,
          background: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 20, flexShrink: 0
        }}>
          ✓
        </div>
        <div>
          <div style={{ fontWeight: 700, fontSize: 18, letterSpacing: '-0.3px' }}>Fact-Checker Pro</div>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.65)', marginTop: 1 }}>
            AI-powered claim verification against live web sources
          </div>
        </div>
      </div>
    </header>
  )
}

function Footer() {
  return (
    <footer style={{ textAlign: 'center', padding: '20px', color: '#9ca3af', fontSize: 12, borderTop: '1px solid #e5e7eb' }}>
      Fact-Checker Pro — Powered by Tavily AI & Supabase
    </footer>
  )
}

function ErrorView({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div style={{ maxWidth: 600, margin: '60px auto', textAlign: 'center' }}>
      <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 12, color: '#b91c1c' }}>Processing Failed</h2>
      <p style={{ color: '#4b5563', marginBottom: 28, lineHeight: 1.6 }}>{message}</p>
      <button
        onClick={onRetry}
        style={{
          background: '#0f62fe', color: '#fff', border: 'none',
          borderRadius: 8, padding: '12px 28px', fontWeight: 600,
          fontSize: 14, cursor: 'pointer',
        }}
      >
        Try Again
      </button>
    </div>
  )
}

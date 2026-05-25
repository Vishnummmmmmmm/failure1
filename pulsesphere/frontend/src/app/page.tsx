'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { useCVIRealtime } from '@/hooks/useCVIRealtime'
import OrgTopBar       from '@/components/OrgBranding'
import CVIGauge        from '@/components/CVIGauge'
import CVITimeline     from '@/components/CVITimeline'
import AlertFeed       from '@/components/AlertFeed'
import PlaybookModal   from '@/components/PlaybookModal'
import EmotionBar      from '@/components/EmotionBar'
import BrandSetup      from '@/components/BrandSetup'
import { triggerCVI, downloadPDF } from '@/lib/api'

export default function Dashboard() {
  const router = useRouter()
  const { userId, email, orgId, branding, loading: authLoading, signOut } = useAuth()

  const [brandId,      setBrandId]      = useState<string | null>(null)
  const [brandName,    setBrandName]    = useState('')
  const [scanning,     setScanning]     = useState(false)
  const [lastEmotions, setLastEmotions] = useState<Record<string,number>>({})

  const { current, history, alerts, connected, refresh } = useCVIRealtime(brandId)

  // Auth gate — redirect to login if not signed in
  useEffect(() => {
    if (!authLoading && !userId) {
      router.replace('/login')
    }
  }, [authLoading, userId])

  function handleBrandCreated(id: string, name: string) {
    setBrandId(id)
    setBrandName(name)
  }

  async function handleScan() {
    if (!brandId) return
    setScanning(true)
    try {
      const result = await triggerCVI(brandId)
      if (result.sources_emotion) setLastEmotions(result.sources_emotion)
    } finally {
      setScanning(false)
    }
  }

  // Accent colour from org branding
  const accent = branding?.accent_color || '#00E5FF'

  if (authLoading) return (
    <div className="min-h-screen bg-[#050509] flex items-center justify-center">
      <div className="text-[#333] font-mono text-sm animate-pulse">LOADING...</div>
    </div>
  )

  if (!userId) return null  // redirecting

  if (!brandId) return (
    <div>
      <OrgTopBar branding={branding} orgId={orgId} email={email} onSignOut={signOut} />
      <BrandSetup onBrandCreated={handleBrandCreated} />
    </div>
  )

  const score        = current?.score    ?? 0
  const level        = current?.level    ?? 'LOW'
  const isAnomaly    = current?.is_anomaly ?? false
  const activeAlertId = alerts[0]?.id

  return (
    <div className="min-h-screen bg-[#050509] text-white">
      <OrgTopBar branding={branding} orgId={orgId} email={email} onSignOut={signOut} />

      {/* Scan + PDF controls */}
      <div className="max-w-7xl mx-auto px-6 pt-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400' : 'bg-red-500'}`} />
          <span className="text-[10px] font-mono text-[#555]">{connected ? 'LIVE' : 'CONNECTING'}</span>
          <span className="text-[#333] font-mono mx-2\">·</span>
          <span className="text-[#555] text-xs font-mono">{brandName.toUpperCase()}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => downloadPDF(brandId)}
            className="text-[10px] font-mono text-[#555] hover:text-[#888] border border-[#1A1A3E] rounded px-2 py-1"
          >PDF REPORT</button>
          <button
            onClick={handleScan} disabled={scanning}
            className={`text-xs font-mono font-bold px-4 py-1.5 rounded-lg border transition-all ${
              scanning ? 'border-[#333] text-[#444] animate-pulse'
              : 'border-[#00E5FF] text-[#00E5FF] hover:bg-[#00E5FF]/10'
            }`}
            style={{ borderColor: scanning ? undefined : accent, color: scanning ? undefined : accent }}
          >
            {scanning ? 'SCANNING...' : '▶ SCAN NOW'}
          </button>
        </div>
      </div>

      {/* Main grid */}
      <div className="max-w-7xl mx-auto p-6 grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-4 bg-[#0A0A1A] border border-[#1A1A3E] rounded-2xl p-6 flex flex-col items-center gap-4">
          <div className="text-[#888] text-xs font-mono tracking-widest self-start">CRISIS VELOCITY INDEX</div>
          <CVIGauge score={score} level={level} isAnomaly={isAnomaly} minutesEarly={18} />
          <div className="w-full grid grid-cols-3 gap-2">
            {[
              { label: 'NEG RATE', value: `${Math.round((current?.neg_rate ?? 0) * 100)}%` },
              { label: 'VELOCITY', value: (current?.velocity ?? 1).toFixed(1) + 'x' },
              { label: 'SPIKE',    value: (current?.spike_factor ?? 1).toFixed(1) + 'x' },
            ].map(s => (
              <div key={s.label} className="bg-[#0D0D1A] rounded-lg p-2 text-center">
                <div className="text-[#555] text-[9px] font-mono">{s.label}</div>
                <div className="text-sm font-bold font-mono" style={{ color: accent }}>{s.value}</div>
              </div>
            ))}
          </div>
          <PlaybookModal brandId={brandId} cviScore={score} alertId={activeAlertId} />
        </div>

        <div className="col-span-12 lg:col-span-8 flex flex-col gap-4">
          <CVITimeline history={history} />
          <div className="bg-[#0A0A1A] border border-[#1A1A3E] rounded-2xl p-5">
            <div className="text-[#888] text-xs font-mono tracking-widest mb-3">ACTIVE ALERTS</div>
            <AlertFeed alerts={alerts} />
          </div>
          {Object.keys(lastEmotions).length > 0 && (
            <div className="bg-[#0A0A1A] border border-[#1A1A3E] rounded-2xl p-5">
              <EmotionBar emotionScores={lastEmotions} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

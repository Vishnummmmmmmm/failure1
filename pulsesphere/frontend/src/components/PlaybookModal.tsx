'use client'
import { useState } from 'react'
import { generatePlaybook, ratePlaybook } from '@/lib/api'

interface Props {
  brandId: string
  cviScore: number
  alertId?: string
}

export default function PlaybookModal({ brandId, cviScore, alertId }: Props) {
  const [open,       setOpen]       = useState(false)
  const [loading,    setLoading]    = useState(false)
  const [playbook,   setPlaybook]   = useState<any>(null)
  const [playbookId, setPlaybookId] = useState<string | null>(null)
  const [rated,      setRated]      = useState<0 | 1 | null>(null)
  const [error,      setError]      = useState('')

  const urgencyColor: Record<string, string> = {
    IMMEDIATE: 'text-red-400',
    '1HR':     'text-orange-400',
    '4HR':     'text-yellow-400',
  }

  async function handleGenerate() {
    setLoading(true); setError('')
    try {
      const result = await generatePlaybook(brandId, cviScore, alertId)
      setPlaybook(result)
      setPlaybookId(result.playbook_id)
      setOpen(true)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleRate(r: 0 | 1) {
    if (!playbookId || rated !== null) return
    await ratePlaybook(playbookId, r)
    setRated(r)
  }

  const locked = cviScore < 75

  return (
    <>
      {/* Trigger button */}
      <button
        onClick={handleGenerate}
        disabled={locked || loading}
        className={`w-full py-3 rounded-xl font-bold text-sm tracking-widest transition-all duration-300 ${
          locked
            ? 'bg-[#111] text-[#333] cursor-not-allowed border border-[#222]'
            : loading
              ? 'bg-red-900 text-red-300 animate-pulse border border-red-700'
              : 'bg-red-600 hover:bg-red-500 text-white border border-red-400 shadow-[0_0_20px_rgba(255,59,59,0.4)]'
        }`}
      >
        {loading ? '⚡ GENERATING PLAYBOOK...' : locked ? `🔒 PLAYBOOK UNLOCKS AT CVI 75 (NOW ${Math.round(cviScore)})` : '🚨 GENERATE CRISIS PLAYBOOK'}
      </button>

      {error && <p className="text-red-400 text-xs mt-1 text-center">{error}</p>}

      {/* Modal overlay */}
      {open && playbook && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0A0A1A] border border-[#FF3B3B] rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b border-[#1A1A3E]">
              <div>
                <div className="text-red-400 text-xs font-mono tracking-widest mb-1">CRISIS PLAYBOOK · CVI {Math.round(cviScore)}</div>
                <div className="text-white font-bold text-lg">{playbook.brand_name}</div>
              </div>
              <button onClick={() => setOpen(false)} className="text-[#555] hover:text-white text-xl">✕</button>
            </div>

            <div className="p-5 space-y-5">

              {/* Crisis Summary */}
              <div className="bg-[#0F0F20] rounded-xl p-4 border border-[#1A1A3E]">
                <div className="text-[#888] text-xs font-mono tracking-widest mb-2">SITUATION ASSESSMENT</div>
                <p className="text-[#CCC] text-sm leading-relaxed">{playbook.crisis_summary}</p>
              </div>

              {/* 3 Actions */}
              <div>
                <div className="text-[#888] text-xs font-mono tracking-widest mb-3">ACTION PLAN</div>
                <div className="space-y-2">
                  {playbook.actions?.map((a: any) => (
                    <div key={a.step} className="flex gap-3 bg-[#0F0F20] rounded-xl p-3 border border-[#1A1A3E]">
                      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-red-900/50 border border-red-700 flex items-center justify-center">
                        <span className="text-red-300 text-xs font-bold">{a.step}</span>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className={`text-[10px] font-bold font-mono ${urgencyColor[a.urgency] || 'text-gray-400'}`}>{a.urgency}</span>
                          <span className="text-[10px] text-[#555] font-mono">{a.owner}</span>
                        </div>
                        <p className="text-[#DDD] text-sm">{a.action}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Press Statement */}
              <div className="bg-[#0F0F20] rounded-xl p-4 border border-[#1A1A3E]">
                <div className="text-[#888] text-xs font-mono tracking-widest mb-2">PRESS STATEMENT · READY TO PUBLISH</div>
                <p className="text-[#AAA] text-sm leading-relaxed italic">{playbook.press_statement}</p>
              </div>

              {/* What not to do */}
              {playbook.what_not_to_do && (
                <div className="bg-yellow-950/40 rounded-xl p-3 border border-yellow-800">
                  <span className="text-yellow-400 text-xs font-mono">⚠ DO NOT: </span>
                  <span className="text-yellow-200 text-sm">{playbook.what_not_to_do}</span>
                </div>
              )}

              {/* Rating */}
              <div className="flex items-center justify-between pt-2 border-t border-[#1A1A3E]">
                <span className="text-[#555] text-xs font-mono">Was this playbook helpful?</span>
                <div className="flex gap-2">
                  {([1, 0] as const).map(r => (
                    <button key={r}
                      onClick={() => handleRate(r)}
                      disabled={rated !== null}
                      className={`px-3 py-1.5 rounded-lg text-sm border transition-all ${
                        rated === r
                          ? r === 1 ? 'bg-green-900 border-green-500 text-green-300' : 'bg-red-900 border-red-500 text-red-300'
                          : rated !== null ? 'opacity-30 cursor-not-allowed border-[#222] text-[#444]'
                          : 'border-[#333] text-[#888] hover:border-[#555] hover:text-white'
                      }`}
                    >
                      {r === 1 ? '👍 Helpful' : '👎 Not helpful'}
                    </button>
                  ))}
                </div>
              </div>
              {rated !== null && (
                <p className="text-center text-[#555] text-xs font-mono">Rating saved · improves future playbooks</p>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

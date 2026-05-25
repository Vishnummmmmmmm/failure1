'use client'
import { useState } from 'react'
import { createBrand, getErrorMessage } from '@/lib/api'

interface Props { onBrandCreated: (id: string, name: string) => void }

export default function BrandSetup({ onBrandCreated }: Props) {
  const [name,     setName]     = useState('')
  const [keywords, setKeywords] = useState('')
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')

  async function handleSubmit() {
    if (!name.trim()) return
    setLoading(true); setError('')
    try {
      const kws    = keywords.split(',').map(k => k.trim()).filter(Boolean)
      const result = await createBrand(name.trim(), kws.length ? kws : [name.trim()])
      onBrandCreated(result.brand_id, result.name)
    } catch (e: unknown) {
      setError(getErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#050509] flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="text-[#00E5FF] text-3xl font-bold font-mono tracking-wider mb-1">PULSESPHERE</div>
          <div className="text-[#444] text-sm font-mono">Crisis Intelligence Platform</div>
        </div>
        <div className="bg-[#0A0A1A] border border-[#1A1A3E] rounded-2xl p-6 space-y-4">
          <div>
            <label className="text-[#888] text-xs font-mono tracking-widest block mb-2">BRAND NAME</label>
            <input
              value={name} onChange={e => setName(e.target.value)}
              placeholder="e.g. Nike, Zomato, HDFC Bank"
              className="w-full bg-[#0D0D1A] border border-[#1A1A3E] rounded-xl px-4 py-3 text-white text-sm font-mono placeholder:text-[#333] focus:outline-none focus:border-[#00E5FF] transition-colors"
            />
          </div>
          <div>
            <label className="text-[#888] text-xs font-mono tracking-widest block mb-2">KEYWORDS <span className="text-[#444]">(comma separated)</span></label>
            <input
              value={keywords} onChange={e => setKeywords(e.target.value)}
              placeholder="Nike, Nike shoes, Just Do It"
              className="w-full bg-[#0D0D1A] border border-[#1A1A3E] rounded-xl px-4 py-3 text-white text-sm font-mono placeholder:text-[#333] focus:outline-none focus:border-[#00E5FF] transition-colors"
            />
          </div>
          {error && <p className="text-red-400 text-xs font-mono">{error}</p>}
          <button
            onClick={handleSubmit} disabled={loading || !name.trim()}
            className="w-full py-3 bg-[#00E5FF] hover:bg-[#00ccee] disabled:bg-[#111] disabled:text-[#333] text-black font-bold rounded-xl font-mono tracking-widest transition-all text-sm"
          >
            {loading ? 'CREATING...' : 'START MONITORING'}
          </button>
        </div>
      </div>
    </div>
  )
}

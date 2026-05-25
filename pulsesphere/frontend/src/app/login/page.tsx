'use client'
import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { useRouter } from 'next/navigation'

export default function LoginPage() {
  const { signIn }   = useAuth()
  const router       = useRouter()
  const [email,    setEmail]    = useState('')
  const [sent,     setSent]     = useState(false)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState('')

  async function handleSubmit() {
    if (!email.trim()) return
    setLoading(true); setError('')
    const { error } = await signIn(email.trim())
    if (error) { setError(error); setLoading(false); return }
    setSent(true)
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-[#050509] flex items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <div className="text-center mb-10">
          <div className="text-[#00E5FF] text-3xl font-bold font-mono tracking-wider mb-2">PULSESPHERE</div>
          <div className="text-[#444] text-sm font-mono">Crisis Intelligence Platform</div>
        </div>

        {sent ? (
          <div className="bg-[#0A0A1A] border border-[#1A1A3E] rounded-2xl p-8 text-center">
            <div className="text-4xl mb-4">📬</div>
            <div className="text-white font-medium mb-2">Check your email</div>
            <div className="text-[#666] text-sm">
              Magic link sent to <span className="text-[#00E5FF]">{email}</span>.
              Click it to sign in — no password needed.
            </div>
            <button
              onClick={() => setSent(false)}
              className="mt-6 text-[#555] text-xs font-mono hover:text-[#888] transition-colors"
            >
              Send again
            </button>
          </div>
        ) : (
          <div className="bg-[#0A0A1A] border border-[#1A1A3E] rounded-2xl p-6 space-y-4">
            <div>
              <label className="text-[#888] text-xs font-mono tracking-widest block mb-2">WORK EMAIL</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                placeholder="you@company.com"
                className="w-full bg-[#0D0D1A] border border-[#1A1A3E] rounded-xl px-4 py-3 text-white text-sm font-mono placeholder:text-[#333] focus:outline-none focus:border-[#00E5FF] transition-colors"
              />
            </div>
            {error && <p className="text-red-400 text-xs font-mono">{error}</p>}
            <button
              onClick={handleSubmit}
              disabled={loading || !email.trim()}
              className="w-full py-3 bg-[#00E5FF] hover:bg-[#00ccee] disabled:bg-[#111] disabled:text-[#333] text-black font-bold rounded-xl font-mono tracking-widest transition-all text-sm"
            >
              {loading ? 'SENDING...' : 'SEND MAGIC LINK'}
            </button>
            <p className="text-center text-[#444] text-xs font-mono pt-1">
              No password. No friction. Just click the link.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { getErrorMessage } from '@/lib/api'
import OrgTopBar         from '@/components/OrgBranding'
import AccentColorPicker from '@/components/AccentColorPicker'

const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function SettingsPage() {
  const router = useRouter()
  const { userId, email, orgId, branding, signOut } = useAuth()
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteSent,  setInviteSent]  = useState(false)
  const [inviteErr,   setInviteErr]   = useState('')
  const [inviting,    setInviting]    = useState(false)

  async function handleInvite() {
    if (!inviteEmail.trim() || !orgId) return
    setInviting(true); setInviteErr('')
    try {
      const r = await fetch(`${BASE}/orgs/${orgId}/invite?email=${encodeURIComponent(inviteEmail)}`, { method: 'POST' })
      if (!r.ok) throw new Error((await r.json()).detail)
      setInviteSent(true)
    } catch (e: unknown) {
      setInviteErr(getErrorMessage(e))
    } finally {
      setInviting(false)
    }
  }

  if (!userId) return null

  return (
    <div className="min-h-screen bg-[#050509] text-white">
      <OrgTopBar branding={branding} orgId={orgId} email={email} onSignOut={signOut} />
      <div className="max-w-2xl mx-auto p-6 space-y-6">

        <div className="flex items-center gap-3 mb-2">
          <button onClick={() => router.push('/')} className="text-[#555] text-xs font-mono hover:text-[#888]">BACK TO DASHBOARD</button>
          <span className="text-[#888] text-xs font-mono">ORG SETTINGS</span>
        </div>

        {/* Accent colour */}
        {orgId && branding && (
          <AccentColorPicker
            orgId={orgId}
            currentColor={branding.accent_color}
          />
        )}

        {/* Invite member */}
        <div className="bg-[#0A0A1A] border border-[#1A1A3E] rounded-xl p-5">
          <div className="text-[#888] text-xs font-mono tracking-widest mb-4">INVITE TEAM MEMBER</div>
          {inviteSent ? (
            <div className="text-green-400 text-sm font-mono">Invite sent to {inviteEmail}</div>
          ) : (
            <div className="flex gap-2">
              <input
                type="email" value={inviteEmail}
                onChange={e => setInviteEmail(e.target.value)}
                placeholder="colleague@company.com"
                className="flex-1 bg-[#0D0D1A] border border-[#1A1A3E] rounded-xl px-4 py-2.5 text-white text-sm font-mono placeholder:text-[#333] focus:outline-none focus:border-[#00E5FF]"
              />
              <button
                onClick={handleInvite} disabled={inviting}
                className="px-4 py-2.5 bg-[#00E5FF] hover:bg-[#00ccee] disabled:bg-[#111] text-black font-bold rounded-xl font-mono text-xs transition-all"
              >
                {inviting ? '...' : 'INVITE'}
              </button>
            </div>
          )}
          {inviteErr && <p className="text-red-400 text-xs font-mono mt-2">{inviteErr}</p>}
        </div>

        {/* Org info */}
        <div className="bg-[#0A0A1A] border border-[#1A1A3E] rounded-xl p-5">
          <div className="text-[#888] text-xs font-mono tracking-widest mb-3">ORG INFO</div>
          <div className="space-y-2 text-sm font-mono">
            <div className="flex justify-between">
              <span className="text-[#555]">Org ID</span>
              <span className="text-[#888]">{orgId?.slice(0,8)}...</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#555]">Plan</span>
              <span className="text-[#00E5FF]">{branding?.plan?.toUpperCase() || 'DEMO'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#555]">Signed in as</span>
              <span className="text-[#888]">{email}</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

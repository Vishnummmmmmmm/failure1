'use client'
import { useRef, useState } from 'react'
import type { OrgBranding } from '@/hooks/useAuth'

interface Props {
  branding:  OrgBranding | null
  orgId:     string | null
  email:     string | null
  onSignOut: () => void
  baseUrl?:  string
}

export default function OrgTopBar({ branding, orgId, email, onSignOut, baseUrl = 'http://localhost:8000' }: Props) {
  const [uploading, setUploading] = useState(false)
  const [logoUrl,   setLogoUrl]   = useState(branding?.white_label_logo_url || null)
  const fileRef = useRef<HTMLInputElement>(null)

  const accent     = branding?.accent_color || '#00E5FF'
  const displayName = branding?.org_display_name || branding?.name || 'PULSESPHERE'

  async function handleLogoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file || !orgId) return
    setUploading(true)
    const form = new FormData()
    form.append('file', file)
    try {
      const r = await fetch(`${baseUrl}/orgs/${orgId}/logo`, { method: 'POST', body: form })
      const data = await r.json()
      if (data.logo_url) {
        setLogoUrl(data.logo_url)
        // Update CSS accent if org has one
        if (branding?.accent_color) {
          document.documentElement.style.setProperty('--ps-accent', branding.accent_color)
        }
      }
    } catch (e) {
      console.error('Logo upload failed', e)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="border-b border-[#0D0D20] px-6 py-3 flex items-center justify-between">
      {/* Left: logo or brand name */}
      <div className="flex items-center gap-3">
        {logoUrl ? (
          <img
            src={logoUrl}
            alt={displayName}
            className="h-7 w-auto object-contain"
            style={{ maxWidth: 120 }}
          />
        ) : (
          <span className="font-bold font-mono tracking-wider text-sm" style={{ color: accent }}>
            {displayName}
          </span>
        )}
        <span className="text-[#333] text-xs font-mono">·</span>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded border" style={{ borderColor: accent + '44', color: accent }}>
          {branding?.plan?.toUpperCase() || 'DEMO'}
        </span>
      </div>

      {/* Right: logo upload + user + signout */}
      <div className="flex items-center gap-3">
        {orgId && (
          <>
            <input
              ref={fileRef} type="file"
              accept="image/png,image/jpeg,image/svg+xml,image/webp"
              className="hidden"
              onChange={handleLogoUpload}
            />
            <button
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              className="text-[10px] font-mono text-[#555] hover:text-[#888] border border-[#1A1A3E] rounded px-2 py-1 transition-colors"
            >
              {uploading ? 'UPLOADING...' : 'UPLOAD LOGO'}
            </button>
          </>
        )}
        {email && (
          <span className="text-[10px] font-mono text-[#444] hidden sm:block">{email}</span>
        )}
        <button
          onClick={onSignOut}
          className="text-[10px] font-mono text-[#555] hover:text-[#888] border border-[#1A1A3E] rounded px-2 py-1 transition-colors"
        >
          SIGN OUT
        </button>
      </div>
    </div>
  )
}

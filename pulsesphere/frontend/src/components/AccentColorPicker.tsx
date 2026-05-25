'use client'
import { useState } from 'react'

const PRESETS = [
  '#00E5FF', '#7F77DD', '#00FF87',
  '#FF3B3B', '#FFB800', '#FF6B35',
  '#A855F7', '#3B82F6', '#EC4899'
]

interface Props {
  orgId:        string
  currentColor: string
  baseUrl?:     string
  onChange?:    (color: string) => void
}

export default function AccentColorPicker({ orgId, currentColor, baseUrl = 'http://localhost:8000', onChange }: Props) {
  const [active,  setActive]  = useState(currentColor)
  const [saving,  setSaving]  = useState(false)

  async function applyColor(color: string) {
    setActive(color)
    document.documentElement.style.setProperty('--ps-accent', color)
    onChange?.(color)
    setSaving(true)
    try {
      await fetch(`${baseUrl}/orgs/${orgId}`, {
        method:  'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ accent_color: color })
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-[#0A0A1A] border border-[#1A1A3E] rounded-xl p-4">
      <div className="text-[#888] text-xs font-mono tracking-widest mb-3">
        BRAND ACCENT COLOUR {saving && <span className="text-[#555]">(saving...)</span>}
      </div>
      <div className="flex flex-wrap gap-2">
        {PRESETS.map(color => (
          <button
            key={color}
            onClick={() => applyColor(color)}
            className="w-7 h-7 rounded-full transition-all"
            style={{
              backgroundColor: color,
              outline: active === color ? `2px solid ${color}` : 'none',
              outlineOffset: 2,
              opacity: active === color ? 1 : 0.6
            }}
          />
        ))}
        <input
          type="color" value={active}
          onChange={e => applyColor(e.target.value)}
          className="w-7 h-7 rounded-full cursor-pointer bg-transparent border-0 p-0"
          title="Custom colour"
        />
      </div>
    </div>
  )
}

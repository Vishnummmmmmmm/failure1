import type { Alert } from '@/hooks/useCVIRealtime'

interface Props { alerts: Alert[] }

const SEV_STYLE: Record<string, string> = {
  CRITICAL: 'bg-red-950    border-red-500    text-red-300',
  HIGH:     'bg-red-950    border-red-700    text-red-400',
  MEDIUM:   'bg-orange-950 border-orange-600 text-orange-300',
  WATCH:    'bg-yellow-950 border-yellow-600 text-yellow-300',
}

export default function AlertFeed({ alerts }: Props) {
  if (!alerts.length) return (
    <div className="text-center text-[#444] text-sm py-8 font-mono">NO ACTIVE ALERTS - CVI STABLE</div>
  )

  return (
    <div className="flex flex-col gap-2">
      {alerts.map(a => (
        <div key={a.id}
          className={`flex items-center justify-between border rounded-lg px-3 py-2 ${SEV_STYLE[a.severity] || 'border-gray-700 text-gray-400'}`}>
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold tracking-widest font-mono">{a.severity}</span>
            <span className="text-xs opacity-70">CVI {Math.round(a.cvi_score)}</span>
            <div className="flex gap-1">
              {a.channels_notified.map(c => (
                <span key={c} className="text-[10px] bg-black/40 rounded px-1 py-0.5 font-mono opacity-60">{c}</span>
              ))}
            </div>
          </div>
          <span className="text-[10px] font-mono opacity-50">
            {new Date(a.triggered_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
      ))}
    </div>
  )
}

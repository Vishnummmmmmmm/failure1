'use client'
import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface BrandCVI {
  brand_id: string
  brand_name: string
  score: number
  level: string
  is_anomaly: boolean
  recorded_at?: string
}

interface CVIHistorySnapshot {
  score: number
  recorded_at: string
}

type HistoryByBrand = Record<string, CVIHistorySnapshot[]>
type ChartPoint = Record<string, number | string>

interface Props {
  brandIds: string[]
  baseUrl?: string
}

const LEVEL_COLOR: Record<string, string> = {
  LOW:      '#00FF87',
  WATCH:    '#FFB800',
  MEDIUM:   '#FF8C00',
  HIGH:     '#FF3B3B',
  CRITICAL: '#FF0000',
}

const LINE_COLORS = ['#00E5FF', '#FF3B3B', '#FFB800']

export default function CompetitorPanel({ brandIds, baseUrl = 'http://localhost:8000' }: Props) {
  const [panel,   setPanel]   = useState<BrandCVI[]>([])
  const [history, setHistory] = useState<HistoryByBrand>({})
  const [wsLive,  setWsLive]  = useState(false)
  const brandIdList = brandIds.join(',')

  // WebSocket for live competitor updates
  useEffect(() => {
    if (!brandIds.length) return
    const wsUrl = `${baseUrl.replace('http', 'ws')}/competitor/ws/competitor?brand_ids=${brandIdList}`
    const ws = new WebSocket(wsUrl)
    ws.onopen  = () => setWsLive(true)
    ws.onclose = () => setWsLive(false)
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data) as { panel?: BrandCVI[] }
      if (data.panel) setPanel(data.panel)
    }
    return () => ws.close()
  }, [baseUrl, brandIdList, brandIds.length])

  // Fetch history for multi-line chart
  useEffect(() => {
    if (!brandIds.length) return
    fetch(`${baseUrl}/competitor/history?brand_ids=${brandIdList}&limit=30`)
      .then(r => r.json())
      .then((data: HistoryByBrand) => setHistory(data))
      .catch(() => {})
  }, [baseUrl, brandIdList, brandIds.length])

  // Merge history into recharts format [{time, Brand1, Brand2, Brand3}]
  const chartData = (() => {
    const names = Object.keys(history)
    if (!names.length) return []
    const maxLen = Math.max(...names.map(n => history[n].length))
    return Array.from({ length: maxLen }, (_, i) => {
      const pt: ChartPoint = { time: '' }
      names.forEach(name => {
        const snap = history[name][i]
        if (snap) {
          pt[name]  = Math.round(snap.score * 10) / 10
          pt.time   = new Date(snap.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      })
      return pt
    })
  })()

  const names = Object.keys(history)

  return (
    <div className="bg-[#0A0A1A] border border-[#1A1A3E] rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <span className="text-[#888] text-xs font-mono tracking-widest">COMPETITOR CVI PANEL</span>
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${wsLive ? 'bg-green-400' : 'bg-red-500'}`} />
          <span className="text-[10px] font-mono text-[#555]">{wsLive ? 'LIVE' : 'OFF'}</span>
        </div>
      </div>

      {/* 3 mini CVI cards */}
      <div className="grid grid-cols-3 gap-3 mb-5">
        {panel.map(b => {
          const color = LEVEL_COLOR[b.level] || '#888'
          return (
            <div key={b.brand_id} className="bg-[#0D0D1A] rounded-xl p-3 border border-[#1A1A3E] text-center">
              <div className="text-[10px] font-mono text-[#555] mb-1 truncate">{b.brand_name.toUpperCase()}</div>
              <div className="text-3xl font-bold font-mono mb-0.5" style={{ color }}>
                {Math.round(b.score)}
              </div>
              <div className="text-[10px] font-mono" style={{ color }}>{b.level}</div>
              {b.is_anomaly && <div className="text-[9px] text-yellow-400 mt-1">anomaly</div>}
            </div>
          )
        })}
      </div>

      {/* Multi-line history */}
      {chartData.length >= 2 && (
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 4, left: -20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#111133" />
            <XAxis dataKey="time" tick={{ fill: '#555', fontSize: 9 }} interval="preserveStartEnd" />
            <YAxis domain={[0, 100]} tick={{ fill: '#555', fontSize: 9 }} />
            <Tooltip
              contentStyle={{ background: '#0A0A1A', border: '1px solid #222244', borderRadius: 8 }}
              labelStyle={{ color: '#888' }}
            />
            <Legend wrapperStyle={{ fontSize: 10, color: '#888' }} />
            {names.map((name, i) => (
              <Line
                key={name} type="monotone" dataKey={name}
                stroke={LINE_COLORS[i % LINE_COLORS.length]}
                strokeWidth={1.5} dot={false} isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'
import type { CVISnapshot } from '@/hooks/useCVIRealtime'

interface Props { history: CVISnapshot[] }

const ZONE_LINES = [
  { y: 90, color: '#FF0000',  label: 'CRITICAL' },
  { y: 75, color: '#FF3B3B',  label: 'HIGH' },
  { y: 60, color: '#FF8C00',  label: 'MEDIUM' },
  { y: 40, color: '#FFB800',  label: 'WATCH' },
]

interface AnomalyDotProps {
  cx?: number
  cy?: number
  payload?: CVISnapshot
}

function AnomalyDot({ cx, cy, payload }: AnomalyDotProps) {
  if (!payload?.is_anomaly || cx === undefined || cy === undefined) return null
  return <circle cx={cx} cy={cy} r={5} fill="#FFB800" stroke="#000" strokeWidth={1} />
}

export default function CVITimeline({ history }: Props) {
  const data = history.map(h => ({
    ...h,
    time:  new Date(h.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    score: Math.round(h.score * 10) / 10
  }))

  return (
    <div className="w-full bg-[#0D0D1A] border border-[#1A1A3E] rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-[#888] text-xs font-mono tracking-widest">CVI TIMELINE - LAST 30 MIN</span>
        <span className="text-[#555] text-xs">anomaly markers</span>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#111133" />
          <XAxis dataKey="time" tick={{ fill: '#555', fontSize: 9 }} interval="preserveStartEnd" />
          <YAxis domain={[0, 100]} tick={{ fill: '#555', fontSize: 9 }} />
          <Tooltip
            contentStyle={{ background: '#0A0A1A', border: '1px solid #222244', borderRadius: 8 }}
            labelStyle={{ color: '#888' }}
            itemStyle={{ color: '#00E5FF' }}
          />
          {ZONE_LINES.map(z => (
            <ReferenceLine key={z.y} y={z.y} stroke={z.color} strokeDasharray="4 4"
              label={{ value: z.label, fill: z.color, fontSize: 8, position: 'right' }} />
          ))}
          <Line
            type="monotone" dataKey="score"
            stroke="#00E5FF" strokeWidth={2} dot={<AnomalyDot />}
            activeDot={{ r: 4, fill: '#00E5FF' }}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

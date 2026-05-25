import { useEffect, useRef } from 'react'

interface Props {
  score: number
  level: string
  isAnomaly?: boolean
  minutesEarly?: number
}

const LEVEL_COLOR: Record<string, string> = {
  LOW:      '#00FF87',
  WATCH:    '#FFB800',
  MEDIUM:   '#FF8C00',
  HIGH:     '#FF3B3B',
  CRITICAL: '#FF0000',
}

function scoreToArc(score: number): string {
  // SVG arc from -210deg to +30deg (240deg sweep)
  const clamp = Math.max(0, Math.min(100, score))
  const sweep  = (clamp / 100) * 240
  const angle  = -210 + sweep
  const rad    = (angle * Math.PI) / 180
  const cx = 100, cy = 100, r = 80
  const x  = cx + r * Math.cos(rad)
  const y  = cy + r * Math.sin(rad)
  const largeArc = sweep > 180 ? 1 : 0
  // Start point at -210deg
  const sx = cx + r * Math.cos((-210 * Math.PI) / 180)
  const sy = cy + r * Math.sin((-210 * Math.PI) / 180)
  return `M ${sx} ${sy} A ${r} ${r} 0 ${largeArc} 1 ${x} ${y}`
}

export default function CVIGauge({ score, level, isAnomaly, minutesEarly }: Props) {
  const pathRef   = useRef<SVGPathElement>(null)
  const prevScore = useRef(score)

  useEffect(() => {
    // Smooth animation between score values
    if (!pathRef.current) return
    const start    = prevScore.current
    const end      = score
    const duration = 600 // ms
    const startTime = performance.now()

    const animate = (now: number) => {
      const t = Math.min((now - startTime) / duration, 1)
      // ease-out cubic
      const eased   = 1 - Math.pow(1 - t, 3)
      const current = start + (end - start) * eased
      if (pathRef.current) {
        pathRef.current.setAttribute('d', scoreToArc(current))
      }
      if (t < 1) requestAnimationFrame(animate)
      else prevScore.current = end
    }
    requestAnimationFrame(animate)
  }, [score])

  const color = LEVEL_COLOR[level] || '#00E5FF'

  return (
    <div className="relative flex flex-col items-center">
      <svg viewBox="0 0 200 160" className="w-64 h-52" role="img" aria-label={`CVI Score ${score}`}>
        {/* Background arc */}
        <path
          d={scoreToArc(100)}
          fill="none" stroke="#1A1A2E" strokeWidth="14" strokeLinecap="round"
        />
        {/* Active arc, animated */}
        <path
          ref={pathRef}
          d={scoreToArc(score)}
          fill="none"
          stroke={color}
          strokeWidth="14"
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 8px ${color})`, transition: 'stroke 0.4s ease' }}
        />
        {/* Score text */}
        <text x="100" y="100" textAnchor="middle" dominantBaseline="middle"
          fill={color} fontSize="36" fontWeight="bold" fontFamily="monospace">
          {Math.round(score)}
        </text>
        {/* Level badge */}
        <text x="100" y="126" textAnchor="middle"
          fill="#888" fontSize="11" fontFamily="monospace" letterSpacing="3">
          {level}
        </text>
        {/* Zone tick marks */}
        {[40, 60, 75, 90].map(v => {
          const ang = (-210 + (v / 100) * 240) * Math.PI / 180
          const x1 = 100 + 88 * Math.cos(ang), y1 = 100 + 88 * Math.sin(ang)
          const x2 = 100 + 72 * Math.cos(ang), y2 = 100 + 72 * Math.sin(ang)
          return <line key={v} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#333355" strokeWidth="1.5" />
        })}
      </svg>
      {/* Pre-echo badge */}
      {isAnomaly && (
        <div className="absolute top-2 right-2 flex items-center gap-1 bg-yellow-900/60 border border-yellow-500 rounded px-2 py-0.5">
          <span className="text-yellow-400 text-xs">Anomaly</span>
          {minutesEarly ? <span className="text-yellow-300 text-xs font-mono">{minutesEarly}m early</span> : null}
        </div>
      )}
    </div>
  )
}

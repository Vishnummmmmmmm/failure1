interface Props { emotionScores: Record<string, number> }

const EMOTION_COLOR: Record<string, string> = {
  anger:    '#FF3B3B',
  disgust:  '#FF6B35',
  fear:     '#FF8C00',
  sadness:  '#5B8CFF',
  surprise: '#A855F7',
  joy:      '#00FF87',
  neutral:  '#444466',
}

export default function EmotionBar({ emotionScores }: Props) {
  const sorted = Object.entries(emotionScores)
    .sort(([,a],[,b]) => b - a)

  return (
    <div className="space-y-1.5">
      <div className="text-[#888] text-xs font-mono tracking-widest mb-3">EMOTION BREAKDOWN</div>
      {sorted.map(([emotion, score]) => (
        <div key={emotion} className="flex items-center gap-2">
          <span className="text-[10px] font-mono w-14 text-right" style={{ color: EMOTION_COLOR[emotion] || '#888' }}>
            {emotion}
          </span>
          <div className="flex-1 bg-[#0D0D1A] rounded-full h-2">
            <div
              className="h-2 rounded-full transition-all duration-500"
              style={{ width: `${Math.round(score * 100)}%`, backgroundColor: EMOTION_COLOR[emotion] || '#444' }}
            />
          </div>
          <span className="text-[10px] font-mono text-[#555] w-8">{Math.round(score * 100)}%</span>
        </div>
      ))}
    </div>
  )
}

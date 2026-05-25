import { useEffect, useState, useCallback } from 'react'
import { supabase } from '@/lib/supabase'
import { fetchCVIHistory, fetchAlerts } from '@/lib/api'

export interface CVISnapshot {
  id: string
  brand_id: string
  score: number
  level: 'LOW' | 'WATCH' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  neg_rate: number
  velocity: number
  spike_factor: number
  is_anomaly: boolean
  recorded_at: string
}

export interface Alert {
  id: string
  severity: string
  cvi_score: number
  triggered_at: string
  channels_notified: string[]
}

export function useCVIRealtime(brandId: string | null) {
  const [current, setCurrent]   = useState<CVISnapshot | null>(null)
  const [history, setHistory]   = useState<CVISnapshot[]>([])
  const [alerts,  setAlerts]    = useState<Alert[]>([])
  const [connected, setConnected] = useState(false)

  // Load initial history on mount
  const loadInitial = useCallback(async () => {
    if (!brandId) return
    const [hist, alrts] = await Promise.all([
      fetchCVIHistory(brandId),
      fetchAlerts(brandId)
    ])
    setHistory(hist)
    setAlerts(alrts)
    if (hist.length > 0) setCurrent(hist[hist.length - 1])
  }, [brandId])

  useEffect(() => {
    if (!brandId) return
    loadInitial()

    // Pure Supabase Realtime WebSocket.
    // No polling. No setInterval. No prefixed timers.
    // Supabase pushes INSERT events via WS the moment backend writes.
    const channel = supabase
      .channel(`cvi_live_${brandId}`)
      .on(
        'postgres_changes',
        {
          event:  'INSERT',
          schema: 'public',
          table:  'cvi_snapshots',
          filter: `brand_id=eq.${brandId}`
        },
        (payload) => {
          const snap = payload.new as CVISnapshot
          // Update current CVI instantly
          setCurrent(snap)
          // Append to history (keep last 30)
          setHistory(prev => [...prev.slice(-29), snap])
          // Re-fetch alerts if HIGH or CRITICAL (new alert may have fired)
          if (snap.score >= 60) {
            fetchAlerts(brandId).then(setAlerts)
          }
        }
      )
      .subscribe((status) => {
        setConnected(status === 'SUBSCRIBED')
      })

    // Cleanup: unsubscribe WS channel on unmount.
    return () => {
      supabase.removeChannel(channel)
    }
  }, [brandId, loadInitial])

  return { current, history, alerts, connected, refresh: loadInitial }
}

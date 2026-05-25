'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { supabase } from '@/lib/supabase'

export default function AuthCallback() {
  const router = useRouter()

  useEffect(() => {
    // Supabase automatically picks up the token from the URL hash
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        router.replace('/')
      } else {
        // Retry once after short delay (token exchange in progress)
        setTimeout(() => {
          supabase.auth.getSession().then(({ data: { session } }) => {
            router.replace(session ? '/' : '/login')
          })
        }, 1500)
      }
    })
  }, [])

  return (
    <div className="min-h-screen bg-[#050509] flex items-center justify-center">
      <div className="text-center">
        <div className="text-[#00E5FF] text-lg font-mono tracking-widest animate-pulse">SIGNING IN...</div>
        <div className="text-[#444] text-xs font-mono mt-2">Verifying magic link</div>
      </div>
    </div>
  )
}

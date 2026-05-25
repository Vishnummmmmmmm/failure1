import { useCallback, useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

export interface OrgBranding {
  id: string
  name: string
  org_display_name: string | null
  accent_color: string
  white_label_logo_url: string | null
  plan: string
}

export interface AuthState {
  userId:    string | null
  email:     string | null
  orgId:     string | null
  branding:  OrgBranding | null
  loading:   boolean
  signIn:    (email: string) => Promise<{ error: string | null }>
  signOut:   () => Promise<void>
}

export function useAuth(): AuthState {
  const [userId,   setUserId]   = useState<string | null>(null)
  const [email,    setEmail]    = useState<string | null>(null)
  const [orgId,    setOrgId]    = useState<string | null>(null)
  const [branding, setBranding] = useState<OrgBranding | null>(null)
  const [loading,  setLoading]  = useState(true)

  const loadOrgForUser = useCallback(async (uid: string) => {
    // Find which org this user belongs to
    const { data: membership } = await supabase
      .from('org_members')
      .select('org_id, role')
      .eq('user_id', uid)
      .limit(1)
      .single()

    if (!membership) return
    setOrgId(membership.org_id)

    // Load org branding
    const { data: org } = await supabase
      .from('orgs')
      .select('id, name, org_display_name, accent_color, white_label_logo_url, plan')
      .eq('id', membership.org_id)
      .single()

    if (org) {
      setBranding(org as OrgBranding)
      // Inject accent colour as CSS variable globally
      document.documentElement.style.setProperty('--ps-accent', org.accent_color || '#00E5FF')
    }
  }, [])

  useEffect(() => {
    // Check existing session
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session?.user) {
        setUserId(session.user.id)
        setEmail(session.user.email ?? null)
        loadOrgForUser(session.user.id).finally(() => setLoading(false))
      } else {
        setLoading(false)
      }
    })

    // Listen for auth changes (magic link callback fires here)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session?.user) {
        setUserId(session.user.id)
        setEmail(session.user.email ?? null)
        await loadOrgForUser(session.user.id)

        // If user was invited (has metadata), ensure org_members row exists
        const invitedOrgId = session.user.user_metadata?.invited_to_org
        if (invitedOrgId) {
          await supabase.from('org_members').upsert({
            org_id:  invitedOrgId,
            user_id: session.user.id,
            role:    'member'
          }, { onConflict: 'org_id,user_id' })
        }
      }
      if (event === 'SIGNED_OUT') {
        setUserId(null); setEmail(null)
        setOrgId(null);  setBranding(null)
        document.documentElement.style.removeProperty('--ps-accent')
      }
    })

    return () => subscription.unsubscribe()
  }, [loadOrgForUser])

  async function signIn(email: string) {
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`
      }
    })
    return { error: error?.message ?? null }
  }

  async function signOut() {
    await supabase.auth.signOut()
  }

  return { userId, email, orgId, branding, loading, signIn, signOut }
}

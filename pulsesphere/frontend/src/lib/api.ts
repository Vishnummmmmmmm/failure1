const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface CVITriggerResult {
  sources_emotion?: Record<string, number>
}

export interface BrandResponse {
  brand_id: string
  name: string
}

export interface PlaybookAction {
  step: number | string
  urgency: string
  owner: string
  action: string
}

export interface PlaybookResponse {
  playbook_id: string
  brand_name: string
  crisis_summary: string
  actions?: PlaybookAction[]
  press_statement: string
  what_not_to_do?: string
}

export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong'
}

export async function triggerCVI(brandId: string): Promise<CVITriggerResult> {
  const r = await fetch(`${BASE}/cvi/?brand_id=${brandId}`)
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function fetchAlerts(brandId: string) {
  const r = await fetch(`${BASE}/alerts/?brand_id=${brandId}&active_only=true`)
  return r.json()
}

export async function fetchCVIHistory(brandId: string) {
  const r = await fetch(`${BASE}/cvi/history?brand_id=${brandId}&limit=30`)
  return r.json()
}

export async function generatePlaybook(
  brandId: string,
  cviScore: number,
  alertId?: string
): Promise<PlaybookResponse> {
  const r = await fetch(`${BASE}/playbook/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ brand_id: brandId, cvi_score: cviScore, alert_id: alertId ?? null })
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function ratePlaybook(playbookId: string, rating: 0 | 1) {
  const r = await fetch(`${BASE}/playbook/${playbookId}/rate`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rating })
  })
  return r.json()
}

export async function createBrand(name: string, keywords: string[]): Promise<BrandResponse> {
  const r = await fetch(`${BASE}/brands/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, keywords })
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export function downloadPDF(brandId: string) {
  window.open(`${BASE}/export/pdf?brand_id=${brandId}`, '_blank')
}

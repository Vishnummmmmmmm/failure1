const BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function triggerCVI(brandId: string) {
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

export async function generatePlaybook(brandId: string, cviScore: number, alertId?: string) {
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

export async function createBrand(name: string, keywords: string[]) {
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

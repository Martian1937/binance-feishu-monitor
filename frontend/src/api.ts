import type { AlertsResponse, PriceAlert } from './types'

async function request<T>(method: string, url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`)
  }
  return res.json() as Promise<T>
}

export const fetchAlerts = () => request<AlertsResponse>('GET', '/api/alerts')

export const upsertAlert = (symbol: string, levels: number[], enabled: boolean) =>
  request<{ alert: PriceAlert; alerts: PriceAlert[] }>('POST', '/api/alerts', {
    symbol,
    levels,
    enabled,
  })

export const removeAlert = (symbol: string) =>
  request<{ ok: boolean; alerts: PriceAlert[] }>('DELETE', `/api/alerts/${encodeURIComponent(symbol)}`)

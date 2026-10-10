export interface PriceAlert {
  symbol: string
  levels: number[]
  enabled: boolean
  last_price: number | null
}

export interface AlertsResponse {
  alerts: PriceAlert[]
  source: string
}

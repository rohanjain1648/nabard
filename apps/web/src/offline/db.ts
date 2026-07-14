import Dexie, { type EntityTable } from 'dexie'
import type { EntryIn, ForecastRow, RiskScore, Alert } from '../api/types'

export interface StoredEntry extends EntryIn {
  synced: 0 | 1
  createdAtLocal: string
}

export interface CacheRow {
  key: string
  value: unknown
  updatedAt: string
}

const db = new Dexie('cashflow-sahayak') as Dexie & {
  entries: EntityTable<StoredEntry, 'id'>
  cache: EntityTable<CacheRow, 'key'>
}

db.version(1).stores({
  entries: 'id, synced, occurred_at',
  cache: 'key',
})

export default db

export async function getDeviceId(): Promise<string> {
  let id = localStorage.getItem('cf_device_id')
  if (!id) {
    id = `WEB-${crypto.randomUUID()}`
    localStorage.setItem('cf_device_id', id)
  }
  return id
}

export async function setCachedForecast(forecast: ForecastRow[]) {
  await db.cache.put({ key: 'forecast', value: forecast, updatedAt: new Date().toISOString() })
}

export async function setCachedRisk(risk: RiskScore | null) {
  await db.cache.put({ key: 'risk', value: risk, updatedAt: new Date().toISOString() })
}

export async function setCachedAlerts(alerts: Alert[]) {
  await db.cache.put({ key: 'alerts', value: alerts, updatedAt: new Date().toISOString() })
}

export async function getCached<T>(key: string): Promise<{ value: T; updatedAt: string } | undefined> {
  const row = await db.cache.get(key)
  if (!row) return undefined
  return { value: row.value as T, updatedAt: row.updatedAt }
}

import client from '../api/client'
import type { EntryIn, SyncResponse } from '../api/types'
import db, { setCachedAlerts, setCachedForecast, setCachedRisk } from './db'

export async function queueEntry(entry: EntryIn) {
  await db.entries.put({ ...entry, synced: 0, createdAtLocal: new Date().toISOString() })
}

export async function getLocalEntries(): Promise<EntryIn[]> {
  const rows = await db.entries.orderBy('occurred_at').reverse().toArray()
  return rows
}

export async function syncNow(): Promise<SyncResponse | null> {
  if (!navigator.onLine) return null

  const pending = await db.entries.where('synced').equals(0).toArray()
  const entries: EntryIn[] = pending.map(({ synced: _synced, createdAtLocal: _createdAtLocal, ...rest }) => rest)

  try {
    const { data } = await client.post<SyncResponse>('/sync', { entries })
    await db.transaction('rw', db.entries, async () => {
      for (const id of data.accepted_ids) {
        await db.entries.update(id, { synced: 1 })
      }
    })
    await setCachedForecast(data.forecast)
    await setCachedRisk(data.risk)
    await setCachedAlerts(data.alerts)
    return data
  } catch (err) {
    // stays queued locally; will retry on next sync trigger (reconnect, interval, manual)
    console.warn('Sync failed, will retry later', err)
    return null
  }
}

export function usePendingCount(): () => Promise<number> {
  return () => db.entries.where('synced').equals(0).count()
}

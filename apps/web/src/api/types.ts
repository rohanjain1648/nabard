export type Role = 'owner' | 'officer'
export type Band = 'green' | 'amber' | 'red' | 'unknown'

export interface LoginResponse {
  token: string
  role: Role
  enterprise_id: string | null
  officer_id: string | null
}

export interface Loan {
  id: string
  principal: number
  outstanding: number
  emi_amount: number
  emi_due_day: number
  start_date: string
  term_months: number
}

export interface EnterpriseProfile {
  id: string
  name: string
  sector: string
  village: string
  district: string
  state: string
  onboarded_at: string
  savings_balance: number
  loans: Loan[]
}

export type EntryType = 'income' | 'expense' | 'savings_deposit' | 'savings_withdrawal' | 'loan_repayment'

export interface EntryIn {
  id: string
  type: EntryType
  category: string
  amount: number
  note?: string | null
  occurred_at: string
  device_id: string
}

export interface ForecastRow {
  target_month: string
  horizon: number
  p10: number
  p50: number
  p90: number
  projected_balance: number
  method: string
}

export interface Driver {
  driver_key: string
  feature: string
  weight: number
  human_text: string
}

export interface RiskScore {
  score: number
  band: Band
  drivers: Driver[]
  as_of: string
}

export interface Alert {
  id: number
  enterprise_id: string
  severity: string
  cause_key: string
  cause_text_en: string
  cause_text_hi: string
  status: string
  created_at: string
}

export interface SyncResponse {
  accepted_ids: string[]
  forecast: ForecastRow[]
  risk: RiskScore | null
  alerts: Alert[]
}

export interface PortfolioItem {
  enterprise_id: string
  name: string
  sector: string
  village: string
  district: string
  band: Band
  score: number
  last_entry_at: string | null
}

export interface PortfolioSummary {
  green: number
  amber: number
  red: number
  total: number
  sector_heatmap: Record<string, Record<string, number>>
}

export interface Categories {
  income: string[]
  expense: string[]
  savings_deposit: string[]
  savings_withdrawal: string[]
  loan_repayment: string[]
}

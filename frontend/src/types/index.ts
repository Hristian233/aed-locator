export type AccessibilityType = '24_7' | 'business_hours' | 'restricted_access'
export type ReportType = 'new_location' | 'aed_issue'

export interface User {
  id: number
  email: string
  full_name: string | null
  role: string
  is_active: boolean
}

export interface AED {
  id: number
  latitude: number
  longitude: number
  address: string | null
  location_name: string | null
  is_restricted_access?: boolean
  description: string | null
  image_url: string | null
  image_urls?: string[]
  verification_status: string
  accessibility_type?: AccessibilityType
  opening_hours?: string | null
  report_type?: ReportType
  contact_email?: string | null
  related_aed_id?: number | null
  distance_meters?: number | null
  ai_confidence?: number | null
  created_at: string
  updated_at: string
}

export interface AEDListResponse {
  items: AED[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface SubmissionResult {
  aed: AED
  warnings: string[]
  duplicate_of_id: number | null
}

export type ReportStatus = 'pending' | 'reviewed' | 'dismissed' | 'resolved'

export interface AEDSummary {
  id: number
  location_name: string | null
  address: string | null
  latitude: number
  longitude: number
  accessibility_type: string
  opening_hours?: string | null
  is_restricted_access: boolean
  image_urls: string[]
}

export interface Report {
  id: number
  aed_id: number | null
  description: string
  reporter_latitude: number | null
  reporter_longitude: number | null
  image_url: string | null
  image_urls?: string[]
  contact_email: string | null
  status: ReportStatus
  spam_score?: number | null
  created_at: string
  updated_at: string
  aed?: AEDSummary | null
}

export interface ReportListResponse {
  items: Report[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface ReportSubmissionResult {
  report: Report
  warnings: string[]
}

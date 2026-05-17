export type AccessibilityType = '24_7' | 'business_hours' | 'restricted_access'
export type ReportType = 'new_location' | 'incorrect_info' | 'unavailable' | 'duplicate'

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
  description: string | null
  image_url: string | null
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

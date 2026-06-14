import type {
  AED,
  AEDListResponse,
  AuthResponse,
  Report,
  ReportListResponse,
  ReportSubmissionResult,
  SubmissionResult,
} from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export type UploadConfig = {
  storage_backend: 'local' | 'gcs'
  environment: 'development' | 'staging' | 'production'
  max_image_bytes: number
  max_images_per_submission: number
  min_images_new_location: number
  allowed_image_types: string[]
  gcs_temp_bucket: string | null
  gcs_images_bucket: string | null
}

export type SignedUploadResponse = {
  upload_url: string
  object_key: string
  expires_in_seconds: number
}

export class ApiError extends Error {
  readonly status: number
  readonly isNetworkError: boolean
  readonly code?: string
  readonly maxImages?: number
  readonly params: Record<string, unknown>

  constructor(
    message: string,
    status: number,
    isNetworkError = false,
    code?: string,
    maxImages?: number,
    params: Record<string, unknown> = {},
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.isNetworkError = isNetworkError
    this.code = code
    this.maxImages = maxImages
    this.params = params
  }
}

export function isServerConnectionError(err: unknown): boolean {
  if (err instanceof ApiError) {
    return err.isNetworkError || err.status >= 500 || err.status === 0
  }
  return err instanceof TypeError
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('aed_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

type ApiErrorDetail = {
  code?: string
  message?: string
  max_images?: number
  max_image_bytes?: number
  [key: string]: unknown
}

function parseErrorDetail(detail: unknown): {
  message: string
  code?: string
  maxImages?: number
  params: Record<string, unknown>
} {
  if (typeof detail === 'string') {
    return { message: detail, params: {} }
  }

  if (Array.isArray(detail)) {
    const message = detail
      .map((item) => {
        if (item && typeof item === 'object' && 'msg' in item) {
          return String((item as { msg: unknown }).msg)
        }
        return String(item)
      })
      .join(' ')
    return { message, params: {} }
  }

  if (detail && typeof detail === 'object') {
    const parsed = detail as ApiErrorDetail
    const message =
      typeof parsed.message === 'string'
        ? parsed.message
        : typeof parsed.code === 'string'
          ? parsed.code
          : JSON.stringify(detail)
    const params: Record<string, unknown> = { ...parsed }
    delete params.code
    delete params.message
    return {
      message,
      code: typeof parsed.code === 'string' ? parsed.code : undefined,
      maxImages: typeof parsed.max_images === 'number' ? parsed.max_images : undefined,
      params,
    }
  }

  return { message: String(detail), params: {} }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...authHeaders(),
        ...options.headers,
      },
    })
  } catch {
    throw new ApiError('Unable to reach the server. Is the API running?', 0, true)
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = body.detail ?? body.message ?? `Request failed (${response.status})`
    const parsed = parseErrorDetail(detail)
    const message =
      response.status === 502
        ? 'Bad gateway — the API server is not responding.'
        : parsed.message
    throw new ApiError(
      message,
      response.status,
      response.status >= 500,
      parsed.code,
      parsed.maxImages,
      parsed.params,
    )
  }

  return response.json() as Promise<T>
}

export const api = {
  health: () => request<{ message: string }>('/health'),

  register: (email: string, password: string, fullName?: string) =>
    request<AuthResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    }),

  login: (email: string, password: string) =>
    request<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<AuthResponse['user']>('/api/v1/auth/me'),

  listAeds: (page = 1, pageSize = 100) =>
    request<AEDListResponse>(`/api/v1/aeds?page=${page}&page_size=${pageSize}`),

  listAllAeds: async () => {
    const pageSize = 100
    let page = 1
    const items: AED[] = []
    while (true) {
      const response = await request<AEDListResponse>(
        `/api/v1/aeds?page=${page}&page_size=${pageSize}`,
      )
      items.push(...response.items)
      if (!response.has_more) break
      page += 1
    }
    return items
  },

  nearestAeds: (
    lat: number,
    lon: number,
    options: {
      limit?: number
      maxDistanceMeters?: number | null
      reachableOnly?: boolean
    } = {},
  ) => {
    const params = new URLSearchParams({
      latitude: String(lat),
      longitude: String(lon),
      limit: String(options.limit ?? 20),
    })
    if (options.maxDistanceMeters != null) {
      params.set('max_distance_meters', String(options.maxDistanceMeters))
    }
    if (options.reachableOnly === false) {
      params.set('reachable_only', 'false')
    }
    return request<AED[]>(`/api/v1/aeds/nearest?${params}`)
  },

  uploadConfig: () => request<UploadConfig>('/api/v1/uploads/config'),

  createSignedUploadUrl: (contentType: string, contentLength: number) =>
    request<SignedUploadResponse>('/api/v1/uploads/signed-url', {
      method: 'POST',
      body: JSON.stringify({ content_type: contentType, content_length: contentLength }),
    }),

  createSignedUploadUrls: (
    uploads: { content_type: string; content_length: number; total_images?: number }[],
  ) =>
    request<{ items: SignedUploadResponse[]; max_images_per_submission: number }>(
      '/api/v1/uploads/signed-urls',
      {
        method: 'POST',
        body: JSON.stringify({ uploads }),
      },
    ),

  uploadToSignedUrl: async (
    uploadUrl: string,
    file: File,
    contentType: string,
  ): Promise<void> => {
    let response: Response
    try {
      response = await fetch(uploadUrl, {
        method: 'PUT',
        headers: { 'Content-Type': contentType },
        body: file,
      })
    } catch {
      throw new ApiError('Image upload failed. Check your connection and try again.', 0, true)
    }
    if (!response.ok) {
      throw new ApiError('Image upload failed. Please try again.', response.status)
    }
  },

  submitAed: (form: FormData) =>
    request<SubmissionResult>('/api/v1/aeds', { method: 'POST', body: form }),

  submitReport: (form: FormData) =>
    request<ReportSubmissionResult>('/api/v1/reports', { method: 'POST', body: form }),

  pendingAeds: (page = 1) =>
    request<AEDListResponse>(`/api/v1/admin/aeds/pending?page=${page}&page_size=20`),

  pendingReports: (page = 1) =>
    request<ReportListResponse>(`/api/v1/admin/reports/pending?page=${page}&page_size=20`),

  verifyAed: (id: number) =>
    request<AED>(`/api/v1/admin/aeds/${id}/verify`, { method: 'POST' }),

  rejectAed: (id: number) =>
    request<AED>(`/api/v1/admin/aeds/${id}/reject`, { method: 'POST' }),

  resolveReport: (id: number) =>
    request<Report>(`/api/v1/admin/reports/${id}/resolve`, { method: 'POST' }),

  dismissReport: (id: number) =>
    request<Report>(`/api/v1/admin/reports/${id}/dismiss`, { method: 'POST' }),
}

export function navigationUrl(lat: number, lon: number, label?: string): string {
  const destination = `${lat},${lon}`
  const encoded = encodeURIComponent(label ?? 'AED')
  if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
    return `https://www.google.com/maps/dir/?api=1&destination=${destination}&destination_place_id=${encoded}`
  }
  return `https://www.google.com/maps/dir/?api=1&destination=${destination}`
}

import type { AED, AEDListResponse, AuthResponse, SubmissionResult } from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

export type UploadConfig = {
  storage_backend: 'local' | 'gcs'
  max_image_bytes: number
  allowed_image_types: string[]
}

export type SignedUploadResponse = {
  upload_url: string
  object_key: string
  expires_in_seconds: number
}

export class ApiError extends Error {
  readonly status: number
  readonly isNetworkError: boolean

  constructor(message: string, status: number, isNetworkError = false) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.isNetworkError = isNetworkError
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
    const message =
      response.status === 502
        ? 'Bad gateway — the API server is not responding.'
        : typeof detail === 'string'
          ? detail
          : String(detail)
    throw new ApiError(message, response.status, response.status >= 500)
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

  pendingAeds: (page = 1) =>
    request<AEDListResponse>(`/api/v1/admin/aeds/pending?page=${page}&page_size=20`),

  verifyAed: (id: number) =>
    request<AED>(`/api/v1/admin/aeds/${id}/verify`, { method: 'POST' }),

  rejectAed: (id: number) =>
    request<AED>(`/api/v1/admin/aeds/${id}/reject`, { method: 'POST' }),
}

export function navigationUrl(lat: number, lon: number, label?: string): string {
  const destination = `${lat},${lon}`
  const encoded = encodeURIComponent(label ?? 'AED')
  if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
    return `https://www.google.com/maps/dir/?api=1&destination=${destination}&destination_place_id=${encoded}`
  }
  return `https://www.google.com/maps/dir/?api=1&destination=${destination}`
}

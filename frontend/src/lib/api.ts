import type { AED, AEDListResponse, AuthResponse, SubmissionResult } from '../types'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('aed_token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...authHeaders(),
      ...options.headers,
    },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail ?? body.message ?? `Request failed (${response.status})`)
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

  nearestAeds: (lat: number, lon: number, limit = 5) =>
    request<AED[]>(
      `/api/v1/aeds/nearest?latitude=${lat}&longitude=${lon}&limit=${limit}&max_distance_meters=10000`,
    ),

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

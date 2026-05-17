import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import type { AED } from '../types'
import { CardSkeleton } from '../components/Skeleton'
import { AccessibilityBadge } from '../components/AccessibilityBadge'

export function AdminPage() {
  const { t } = useTranslation()
  const { isAdmin, loading: authLoading } = useAuth()
  const [pending, setPending] = useState<AED[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.pendingAeds()
      setPending(res.items)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('admin.loadFailed'))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    if (isAdmin) load()
  }, [isAdmin, load])

  if (authLoading) return null
  if (!isAdmin) return <Navigate to="/auth" replace />

  const verify = async (id: number) => {
    await api.verifyAed(id)
    setPending((list) => list.filter((a) => a.id !== id))
  }

  const reject = async (id: number) => {
    await api.rejectAed(id)
    setPending((list) => list.filter((a) => a.id !== id))
  }

  return (
    <div className="mx-auto max-w-2xl flex-1 overflow-y-auto p-4 pb-12">
      <h1 className="text-2xl font-bold text-slate-900">{t('admin.title')}</h1>
      <p className="text-sm text-slate-600">{t('admin.subtitle')}</p>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-6 space-y-4">
        {loading ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : pending.length === 0 ? (
          <p className="text-slate-600">{t('admin.empty')}</p>
        ) : (
          pending.map((aed) => (
            <article
              key={aed.id}
              className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200"
            >
              <h2 className="font-semibold">
                {aed.address ?? t('aed.fallbackName', { id: aed.id })}
              </h2>
              <p className="text-sm text-slate-600">
                {aed.latitude.toFixed(5)}, {aed.longitude.toFixed(5)}
              </p>
              {aed.report_type && (
                <p className="mt-1 text-xs text-slate-500">
                  {t('admin.reportType', {
                    type: t(`report.types.${aed.report_type}`, { defaultValue: aed.report_type }),
                  })}
                </p>
              )}
              {aed.contact_email && (
                <p className="text-xs text-slate-500">
                  {t('admin.contactEmail', { email: aed.contact_email })}
                </p>
              )}
              <div className="mt-2">
                <AccessibilityBadge aed={aed} />
              </div>
              {aed.opening_hours && (
                <p className="mt-1 text-xs text-slate-500">
                  {t('admin.openingHours')}: {aed.opening_hours}
                </p>
              )}
              {aed.description && (
                <p className="mt-2 text-sm text-slate-700">{aed.description}</p>
              )}
              {aed.ai_confidence != null && (
                <p className="mt-1 text-xs text-slate-500">
                  {t('admin.aiConfidence', {
                    percent: (aed.ai_confidence * 100).toFixed(0),
                  })}
                </p>
              )}
              {aed.image_url && (
                <img
                  src={aed.image_url}
                  alt={t('admin.submittedImage')}
                  className="mt-3 max-h-40 rounded-lg object-cover"
                />
              )}
              <div className="mt-4 flex gap-2">
                <button
                  type="button"
                  onClick={() => verify(aed.id)}
                  className="flex-1 rounded-xl bg-emerald-600 py-2 text-sm font-semibold text-white"
                >
                  {t('admin.verify')}
                </button>
                <button
                  type="button"
                  onClick={() => reject(aed.id)}
                  className="flex-1 rounded-xl border border-slate-200 py-2 text-sm font-semibold text-slate-700"
                >
                  {t('admin.reject')}
                </button>
              </div>
            </article>
          ))
        )}
      </div>
    </div>
  )
}

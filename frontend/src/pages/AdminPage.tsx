import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { api } from '../lib/api'
import { formatApiError } from '../lib/apiErrors'
import { FormErrorAlert } from '../components/FormErrorAlert'
import { formatAedPrimaryName } from '../lib/aedLabel'
import type { AED, Report } from '../types'
import { CardSkeleton } from '../components/Skeleton'
import { AccessibilityBadge } from '../components/AccessibilityBadge'

type AdminTab = 'aeds' | 'reports'

export function AdminPage() {
  const { t } = useTranslation()
  const { isAdmin, loading: authLoading } = useAuth()
  const [tab, setTab] = useState<AdminTab>('aeds')
  const [pendingAeds, setPendingAeds] = useState<AED[]>([])
  const [pendingReports, setPendingReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<ReturnType<typeof formatApiError> | null>(null)

  const loadAeds = useCallback(async () => {
    const res = await api.pendingAeds()
    setPendingAeds(res.items)
  }, [])

  const loadReports = useCallback(async () => {
    const res = await api.pendingReports()
    setPendingReports(res.items)
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      if (tab === 'aeds') {
        await loadAeds()
      } else {
        await loadReports()
      }
    } catch (err) {
      setError(formatApiError(err, t, { context: 'admin' }))
    } finally {
      setLoading(false)
    }
  }, [loadAeds, loadReports, tab, t])

  useEffect(() => {
    if (isAdmin) load()
  }, [isAdmin, load])

  if (authLoading) return null
  if (!isAdmin) return <Navigate to="/auth" replace />

  const verify = async (id: number) => {
    await api.verifyAed(id)
    setPendingAeds((list) => list.filter((a) => a.id !== id))
  }

  const reject = async (id: number) => {
    await api.rejectAed(id)
    setPendingAeds((list) => list.filter((a) => a.id !== id))
  }

  const resolveReport = async (id: number) => {
    await api.resolveReport(id)
    setPendingReports((list) => list.filter((r) => r.id !== id))
  }

  const dismissReport = async (id: number) => {
    await api.dismissReport(id)
    setPendingReports((list) => list.filter((r) => r.id !== id))
  }

  return (
    <div className="mx-auto max-w-2xl flex-1 overflow-y-auto p-4 pb-12">
      <h1 className="text-2xl font-bold text-slate-900">{t('admin.title')}</h1>
      <p className="text-sm text-slate-600">{t('admin.subtitle')}</p>

      <div className="mt-4 flex gap-2 rounded-xl bg-slate-100 p-1">
        <button
          type="button"
          onClick={() => setTab('aeds')}
          className={`flex-1 rounded-lg px-3 py-2 text-sm font-semibold ${
            tab === 'aeds' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'
          }`}
        >
          {t('admin.tabs.aeds')}
        </button>
        <button
          type="button"
          onClick={() => setTab('reports')}
          className={`flex-1 rounded-lg px-3 py-2 text-sm font-semibold ${
            tab === 'reports' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-600'
          }`}
        >
          {t('admin.tabs.reports')}
        </button>
      </div>

      {error && (
        <div className="mt-4">
          <FormErrorAlert {...error} />
        </div>
      )}

      <div className="mt-6 space-y-4">
        {loading ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : tab === 'aeds' ? (
          pendingAeds.length === 0 ? (
            <p className="text-slate-600">{t('admin.emptyAeds')}</p>
          ) : (
            pendingAeds.map((aed) => (
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
                      type: t(`report.types.${aed.report_type}`, {
                        defaultValue: aed.report_type,
                      }),
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
                {(aed.image_urls?.length ? aed.image_urls : aed.image_url ? [aed.image_url] : [])
                  .length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(aed.image_urls?.length
                      ? aed.image_urls
                      : aed.image_url
                        ? [aed.image_url]
                        : []
                    ).map((url) => (
                      <img
                        key={url}
                        src={url}
                        alt={t('admin.submittedImage')}
                        className="max-h-40 rounded-lg object-cover"
                      />
                    ))}
                  </div>
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
          )
        ) : pendingReports.length === 0 ? (
          <p className="text-slate-600">{t('admin.emptyReports')}</p>
        ) : (
          pendingReports.map((report) => {
            const reportImages = report.image_urls?.length
              ? report.image_urls
              : report.image_url
                ? [report.image_url]
                : []

            return (
              <article
                key={report.id}
                className="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200"
              >
                <p className="text-xs text-slate-500">
                  {t('admin.submittedAt', {
                    date: new Date(report.created_at).toLocaleString(),
                  })}
                </p>

                <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    {t('admin.linkedAed')}
                  </p>
                  {report.aed ? (
                    <>
                      <p className="mt-1 font-semibold text-slate-900">
                        {formatAedPrimaryName(report.aed, t)}
                      </p>
                      {report.aed.address && (
                        <p className="text-sm text-slate-600">{report.aed.address}</p>
                      )}
                      <p className="mt-1 text-xs text-slate-500">
                        {report.aed.latitude.toFixed(5)}, {report.aed.longitude.toFixed(5)}
                      </p>
                      <div className="mt-2">
                        <AccessibilityBadge aed={report.aed as AED} compact />
                      </div>
                    </>
                  ) : (
                    <p className="mt-1 text-sm text-slate-600">{t('admin.noLinkedAed')}</p>
                  )}
                </div>

                <p className="mt-4 text-base font-medium text-slate-900">{report.description}</p>

                {report.reporter_latitude != null && report.reporter_longitude != null && (
                  <p className="mt-2 text-sm text-slate-600">
                    {t('admin.reporterLocation', {
                      lat: report.reporter_latitude.toFixed(5),
                      lon: report.reporter_longitude.toFixed(5),
                    })}
                  </p>
                )}

                {report.contact_email && (
                  <p className="mt-2 text-sm text-slate-600">
                    {t('admin.contactEmail', { email: report.contact_email })}
                  </p>
                )}

                {reportImages.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {reportImages.map((url) => (
                      <img
                        key={url}
                        src={url}
                        alt={t('admin.reportImage')}
                        className="max-h-40 rounded-lg object-cover"
                      />
                    ))}
                  </div>
                )}

                <div className="mt-4 flex gap-2">
                  <button
                    type="button"
                    onClick={() => resolveReport(report.id)}
                    className="flex-1 rounded-xl bg-emerald-600 py-2 text-sm font-semibold text-white"
                  >
                    {t('admin.resolve')}
                  </button>
                  <button
                    type="button"
                    onClick={() => dismissReport(report.id)}
                    className="flex-1 rounded-xl border border-slate-200 py-2 text-sm font-semibold text-slate-700"
                  >
                    {t('admin.dismiss')}
                  </button>
                </div>
              </article>
            )
          })
        )}
      </div>
    </div>
  )
}

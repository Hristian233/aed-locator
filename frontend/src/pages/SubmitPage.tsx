import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import type { AccessibilityType, ReportType } from '../types'

const REPORT_TYPES: ReportType[] = [
  'new_location',
  'incorrect_info',
  'unavailable',
  'duplicate',
]

const ACCESSIBILITY_TYPES: AccessibilityType[] = ['24_7', 'business_hours', 'restricted_access']

const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export function SubmitPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [reportType, setReportType] = useState<ReportType>('new_location')
  const [latitude, setLatitude] = useState<number | null>(null)
  const [longitude, setLongitude] = useState<number | null>(null)
  const [address, setAddress] = useState('')
  const [description, setDescription] = useState('')
  const [relatedAedId, setRelatedAedId] = useState('')
  const [accessibilityType, setAccessibilityType] = useState<AccessibilityType>('24_7')
  const [openingHours, setOpeningHours] = useState('')
  const [contactEmail, setContactEmail] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])
  const [submitted, setSubmitted] = useState(false)

  const captureLocation = () => {
    if (!('geolocation' in navigator)) {
      setError(t('report.errors.geoUnsupported'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude)
        setLongitude(pos.coords.longitude)
        setError(null)
      },
      () => setError(t('report.errors.geoFailed')),
      { enableHighAccuracy: true },
    )
  }

  const validateImage = (file: File | null): string | null => {
    if (!file) return null
    if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
      return t('report.errors.imageType')
    }
    if (file.size < 1024) {
      return t('report.errors.imageTooSmall')
    }
    return null
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (latitude == null || longitude == null) {
      setError(t('report.errors.locationRequired'))
      return
    }
    const imageError = validateImage(image)
    if (imageError) {
      setError(imageError)
      return
    }

    setLoading(true)
    setError(null)
    setWarnings([])
    try {
      const form = new FormData()
      form.append('latitude', String(latitude))
      form.append('longitude', String(longitude))
      form.append('report_type', reportType)
      form.append('accessibility_type', accessibilityType)
      if (address) form.append('address', address)
      if (description) form.append('description', description)
      if (openingHours.trim()) form.append('opening_hours', openingHours.trim())
      if (contactEmail.trim()) form.append('contact_email', contactEmail.trim())
      if (relatedAedId.trim()) form.append('related_aed_id', relatedAedId.trim())
      if (image) form.append('image', image)

      const result = await api.submitAed(form)
      setWarnings(result.warnings)
      setSubmitted(true)
      setTimeout(() => navigate('/'), 2500)
    } catch (err) {
      setError(err instanceof Error ? err.message : t('report.errors.submissionFailed'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-lg flex-1 overflow-y-auto p-4 pb-12">
      <h1 className="text-2xl font-bold text-slate-900">{t('report.title')}</h1>
      <p className="mt-1 text-sm text-slate-600">{t('report.subtitle')}</p>

      {submitted && (
        <p className="mt-4 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-900" role="status">
          {t('report.successRedirect')}
        </p>
      )}

      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <fieldset>
          <legend className="text-sm font-medium text-slate-700">{t('report.typeLabel')}</legend>
          <div className="mt-2 space-y-2">
            {REPORT_TYPES.map((type) => (
              <label
                key={type}
                className={`flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-2.5 text-sm ${
                  reportType === type
                    ? 'border-teal-500 bg-teal-50 text-teal-900'
                    : 'border-slate-200 bg-white text-slate-700'
                }`}
              >
                <input
                  type="radio"
                  name="report_type"
                  value={type}
                  checked={reportType === type}
                  onChange={() => setReportType(type)}
                  className="text-teal-600"
                />
                {t(`report.types.${type}`)}
              </label>
            ))}
          </div>
        </fieldset>

        <div>
          <button
            type="button"
            onClick={captureLocation}
            className="w-full rounded-xl border-2 border-dashed border-teal-300 bg-teal-50 py-4 text-sm font-semibold text-teal-800"
          >
            {latitude != null
              ? t('report.locationCaptured', {
                  lat: latitude.toFixed(5),
                  lon: longitude?.toFixed(5),
                })
              : t('report.useLocation')}
          </button>
        </div>

        {(reportType === 'incorrect_info' ||
          reportType === 'unavailable' ||
          reportType === 'duplicate') && (
          <label className="block">
            <span className="text-sm font-medium text-slate-700">{t('report.relatedAed')}</span>
            <input
              type="number"
              min={1}
              value={relatedAedId}
              onChange={(e) => setRelatedAedId(e.target.value)}
              className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
              placeholder={t('report.relatedAedPlaceholder')}
            />
          </label>
        )}

        <label className="block">
          <span className="text-sm font-medium text-slate-700">{t('report.address')}</span>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
            placeholder={t('report.addressPlaceholder')}
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-slate-700">{t('report.description')}</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
            placeholder={t('report.descriptionPlaceholder')}
          />
        </label>

        {reportType === 'new_location' && (
          <>
            <label className="block">
              <span className="text-sm font-medium text-slate-700">{t('report.accessibility')}</span>
              <select
                value={accessibilityType}
                onChange={(e) => setAccessibilityType(e.target.value as AccessibilityType)}
                className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
              >
                {ACCESSIBILITY_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {t(`report.accessibilityTypes.${type}`)}
                  </option>
                ))}
              </select>
            </label>

            {accessibilityType === 'business_hours' && (
              <label className="block">
                <span className="text-sm font-medium text-slate-700">{t('report.openingHours')}</span>
                <textarea
                  value={openingHours}
                  onChange={(e) => setOpeningHours(e.target.value)}
                  rows={3}
                  className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 font-mono text-xs"
                  placeholder={t('report.openingHoursPlaceholder')}
                />
                <p className="mt-1 text-xs text-slate-500">{t('report.openingHoursHelp')}</p>
              </label>
            )}
          </>
        )}

        <label className="block">
          <span className="text-sm font-medium text-slate-700">{t('report.photo')}</span>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            onChange={(e) => {
              const file = e.target.files?.[0] ?? null
              setImage(file)
              setError(validateImage(file))
            }}
            className="mt-1 w-full text-sm"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-slate-700">{t('report.email')}</span>
          <input
            type="email"
            value={contactEmail}
            onChange={(e) => setContactEmail(e.target.value)}
            autoComplete="email"
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
            placeholder={t('report.emailPlaceholder')}
          />
        </label>

        {error && (
          <p className="text-sm text-red-600" role="alert">
            {error}
          </p>
        )}
        {warnings.length > 0 && (
          <ul className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
            {warnings.map((w) => (
              <li key={w}>• {w}</li>
            ))}
          </ul>
        )}

        <button
          type="submit"
          disabled={loading || submitted}
          className="w-full rounded-xl bg-teal-600 py-3 font-semibold text-white disabled:opacity-60"
        >
          {loading ? t('report.submitting') : t('report.submit')}
        </button>
      </form>
    </div>
  )
}

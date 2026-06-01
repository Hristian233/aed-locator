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

const WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'] as const
type WeekdayKey = (typeof WEEKDAYS)[number]

const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

const HOURS = Array.from({ length: 24 }, (_, index) => String(index).padStart(2, '0'))
const MINUTES = Array.from({ length: 60 }, (_, index) => String(index).padStart(2, '0'))

type TimeSelection = { hour: string; minute: string }
type DayHours = { open: TimeSelection; close: TimeSelection }
type WeeklyHours = Record<WeekdayKey, DayHours>

const EMPTY_TIME: TimeSelection = { hour: '', minute: '' }

function emptyWeeklyHours(): WeeklyHours {
  return {
    mon: { open: { ...EMPTY_TIME }, close: { ...EMPTY_TIME } },
    tue: { open: { ...EMPTY_TIME }, close: { ...EMPTY_TIME } },
    wed: { open: { ...EMPTY_TIME }, close: { ...EMPTY_TIME } },
    thu: { open: { ...EMPTY_TIME }, close: { ...EMPTY_TIME } },
    fri: { open: { ...EMPTY_TIME }, close: { ...EMPTY_TIME } },
    sat: { open: { ...EMPTY_TIME }, close: { ...EMPTY_TIME } },
    sun: { open: { ...EMPTY_TIME }, close: { ...EMPTY_TIME } },
  }
}

function isTimeEmpty(time: TimeSelection): boolean {
  return !time.hour && !time.minute
}

function isTimePartial(time: TimeSelection): boolean {
  return Boolean(time.hour) !== Boolean(time.minute)
}

function isTimeComplete(time: TimeSelection): boolean {
  return Boolean(time.hour && time.minute)
}

function formatTimeSelection(time: TimeSelection): string {
  if (!isTimeComplete(time)) return ''
  return `${time.hour}:${time.minute}`
}

function validateWeeklyHours(hours: WeeklyHours): 'partial' | 'required' | null {
  let hasCompleteDay = false
  for (const day of WEEKDAYS) {
    const { open, close } = hours[day]
    if (isTimePartial(open) || isTimePartial(close)) return 'partial'
    if (isTimeComplete(open) && isTimeComplete(close)) {
      hasCompleteDay = true
      continue
    }
    if (!isTimeEmpty(open) || !isTimeEmpty(close)) return 'partial'
  }
  return hasCompleteDay ? null : 'required'
}

function serializeWeeklyHours(hours: WeeklyHours): string | null {
  const data: Record<string, { open: string; close: string }> = {}
  for (const day of WEEKDAYS) {
    const open = formatTimeSelection(hours[day].open)
    const close = formatTimeSelection(hours[day].close)
    if (open && close) {
      data[day] = { open, close }
    } else if (open || close) {
      return null
    }
  }
  return Object.keys(data).length > 0 ? JSON.stringify(data) : null
}

function TimeDropdowns({
  value,
  onChange,
  label,
}: {
  value: TimeSelection
  onChange: (value: TimeSelection) => void
  label: string
}) {
  const { t } = useTranslation()

  return (
    <div className="flex items-center gap-1" role="group" aria-label={label}>
      <select
        value={value.hour}
        onChange={(e) => onChange({ ...value, hour: e.target.value })}
        aria-label={`${label} — ${t('report.hour')}`}
        className="min-w-0 flex-1 rounded-lg border border-slate-200 px-1.5 py-1.5 text-sm"
      >
        <option value="">{t('report.timeUnset')}</option>
        {HOURS.map((hour) => (
          <option key={hour} value={hour}>
            {hour}
          </option>
        ))}
      </select>
      <span aria-hidden="true" className="text-slate-400">
        :
      </span>
      <select
        value={value.minute}
        onChange={(e) => onChange({ ...value, minute: e.target.value })}
        aria-label={`${label} — ${t('report.minute')}`}
        className="min-w-0 flex-1 rounded-lg border border-slate-200 px-1.5 py-1.5 text-sm"
      >
        <option value="">{t('report.timeUnset')}</option>
        {MINUTES.map((minute) => (
          <option key={minute} value={minute}>
            {minute}
          </option>
        ))}
      </select>
    </div>
  )
}

export function SubmitPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [reportType, setReportType] = useState<ReportType>('new_location')
  const [latitude, setLatitude] = useState<number | null>(null)
  const [longitude, setLongitude] = useState<number | null>(null)
  const [address, setAddress] = useState('')
  const [description, setDescription] = useState('')
  const [relatedAedId, setRelatedAedId] = useState('')
  const [accessibilityType, setAccessibilityType] = useState<AccessibilityType | ''>('')
  const [weeklyHours, setWeeklyHours] = useState<WeeklyHours>(emptyWeeklyHours)
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

  const updateDayHours = (
    day: WeekdayKey,
    field: keyof DayHours,
    value: TimeSelection,
  ) => {
    setWeeklyHours((current) => ({
      ...current,
      [day]: { ...current[day], [field]: value },
    }))
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

    let openingHours: string | null = null
    if (reportType === 'new_location') {
      if (!accessibilityType) {
        setError(t('report.errors.accessibilityRequired'))
        return
      }
      if (accessibilityType === 'business_hours') {
        const hoursError = validateWeeklyHours(weeklyHours)
        if (hoursError) {
          setError(
            hoursError === 'partial'
              ? t('report.errors.openingHoursIncomplete')
              : t('report.errors.openingHoursRequired'),
          )
          return
        }
        openingHours = serializeWeeklyHours(weeklyHours)
      }
    }

    setLoading(true)
    setError(null)
    setWarnings([])
    try {
      const form = new FormData()
      form.append('latitude', String(latitude))
      form.append('longitude', String(longitude))
      form.append('report_type', reportType)
      if (reportType === 'new_location' && accessibilityType) {
        form.append('accessibility_type', accessibilityType)
        if (openingHours) form.append('opening_hours', openingHours)
      }
      if (address) form.append('address', address)
      if (description) form.append('description', description)
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
          {reportType === 'new_location' && (
            <p className="mt-2 text-center text-sm text-slate-500">
              {t('report.locationOnSiteHint')}
            </p>
          )}
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
                onChange={(e) => {
                  const value = e.target.value as AccessibilityType | ''
                  setAccessibilityType(value)
                  if (value !== 'business_hours') {
                    setWeeklyHours(emptyWeeklyHours())
                  }
                }}
                required
                className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
              >
                <option value="" disabled hidden>
                  {t('report.accessibilityPlaceholder')}
                </option>
                {ACCESSIBILITY_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {t(`report.accessibilityTypes.${type}`)}
                  </option>
                ))}
              </select>
            </label>

            {accessibilityType === 'business_hours' && (
              <fieldset className="space-y-3">
                <legend className="text-sm font-medium text-slate-700">{t('report.openingHours')}</legend>
                <p id="opening-hours-format-help" className="text-xs text-slate-600">
                  {t('report.openingHoursFormat')}
                </p>
                <div className="grid grid-cols-[minmax(4.5rem,5.5rem)_1fr_1fr] items-center gap-2 px-1 text-xs font-medium text-slate-500 sm:px-3">
                  <span aria-hidden="true" />
                  <span>{t('report.openColumn')}</span>
                  <span>{t('report.closeColumn')}</span>
                </div>
                <div className="space-y-2">
                  {WEEKDAYS.map((day) => (
                    <div
                      key={day}
                      className="grid grid-cols-[minmax(4.5rem,5.5rem)_1fr_1fr] items-center gap-2 rounded-xl border border-slate-200 bg-white px-2 py-2 sm:px-3"
                    >
                      <span className="text-sm font-medium text-slate-700">
                        {t(`report.weekdays.${day}`)}
                      </span>
                      <TimeDropdowns
                        value={weeklyHours[day].open}
                        onChange={(value) => updateDayHours(day, 'open', value)}
                        label={t('report.openTime', { day: t(`report.weekdays.${day}`) })}
                      />
                      <TimeDropdowns
                        value={weeklyHours[day].close}
                        onChange={(value) => updateDayHours(day, 'close', value)}
                        label={t('report.closeTime', { day: t(`report.weekdays.${day}`) })}
                      />
                    </div>
                  ))}
                </div>
                <p className="text-xs text-slate-500">{t('report.openingHoursHelp')}</p>
              </fieldset>
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
          className="w-full cursor-pointer rounded-xl bg-teal-600 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? t('report.submitting') : t('report.submit')}
        </button>
      </form>
    </div>
  )
}

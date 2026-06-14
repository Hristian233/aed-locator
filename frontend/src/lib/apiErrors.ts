import { ApiError } from './api'

export type FormErrorDisplay = {
  title?: string
  message: string
  detail?: string
}

export type SubmissionWarning = {
  code: string
  params?: Record<string, string | number>
}

type TranslateFn = (key: string, options?: Record<string, unknown>) => string

export type ApiErrorContext = 'submit' | 'auth' | 'admin' | 'generic'

const UNHELPFUL_API_MESSAGES = [
  /^Request failed \(\d+\)$/,
  /^Internal [Ss]erver [Ee]rror$/,
  /^Bad gateway/,
  /^Service [Uu]navailable$/,
  /^Gateway [Tt]imeout$/,
]

const API_ERROR_KEYS: Record<string, string> = {
  image_required: 'apiErrors.imageRequired',
  opening_hours_required: 'apiErrors.openingHoursRequired',
  opening_hours_invalid: 'apiErrors.openingHoursInvalid',
  wrong_report_endpoint: 'apiErrors.wrongReportEndpoint',
  description_required: 'apiErrors.descriptionRequired',
  restricted_description_required: 'apiErrors.restrictedDescriptionRequired',
  related_aed_not_found: 'apiErrors.relatedAedNotFound',
  spam_detected: 'apiErrors.spamDetected',
  gcs_upload_required: 'apiErrors.gcsUploadRequired',
  temp_keys_gcs_only: 'apiErrors.tempKeysGcsOnly',
  image_type_invalid: 'apiErrors.imageType',
  image_too_small: 'apiErrors.imageTooSmall',
  image_too_large: 'apiErrors.imageTooLarge',
  image_invalid: 'apiErrors.imageInvalid',
  image_processing_failed: 'apiErrors.imageProcessingFailed',
  reporter_location_incomplete: 'apiErrors.reporterLocationIncomplete',
  email_registered: 'apiErrors.emailRegistered',
  invalid_credentials: 'apiErrors.invalidCredentials',
  account_disabled: 'apiErrors.accountDisabled',
  auth_failed: 'apiErrors.authFailed',
  not_authenticated: 'apiErrors.notAuthenticated',
  admin_required: 'apiErrors.adminRequired',
  aed_not_found: 'apiErrors.aedNotFound',
  report_not_found: 'apiErrors.reportNotFound',
  direct_upload_disabled: 'apiErrors.directUploadDisabled',
  storage_unavailable: 'apiErrors.storageUnavailable',
  unknown: 'apiErrors.unknown',
}

const WARNING_KEYS: Record<string, string> = {
  pending_review: 'apiWarnings.pendingReview',
  duplicate_nearby: 'apiWarnings.duplicateNearby',
}

export function isUnhelpfulApiMessage(message: string): boolean {
  const trimmed = message.trim()
  if (!trimmed) return true
  return UNHELPFUL_API_MESSAGES.some((pattern) => pattern.test(trimmed))
}

export function simpleFormError(message: string): FormErrorDisplay {
  return { message }
}

function translateErrorCode(
  code: string | undefined,
  params: Record<string, unknown>,
  t: TranslateFn,
  maxImages?: number,
): string | null {
  if (!code) return null
  if (code === 'image_too_many') {
    const max = typeof params.max_images === 'number' ? params.max_images : maxImages
    return t('report.errors.imageTooMany', { max: max ?? maxImages ?? 5 })
  }
  const key = API_ERROR_KEYS[code]
  if (!key) return null
  if (code === 'image_too_large' && typeof params.max_image_bytes === 'number') {
    const maxMb = Math.max(1, Math.round(Number(params.max_image_bytes) / (1024 * 1024)))
    return t(key, { maxMb })
  }
  if (code === 'duplicate_nearby' && typeof params.meters === 'number') {
    return t('apiWarnings.duplicateNearby', { meters: params.meters })
  }
  return t(key, params)
}

function contextTitle(context: ApiErrorContext, t: TranslateFn): string | undefined {
  switch (context) {
    case 'submit':
      return t('report.errors.submissionFailedTitle')
    case 'auth':
      return undefined
    case 'admin':
      return t('admin.loadFailedTitle')
    default:
      return t('common.errorTitle')
  }
}

export function formatApiError(
  err: unknown,
  t: TranslateFn,
  options: {
    context?: ApiErrorContext
    maxImages?: number
  } = {},
): FormErrorDisplay {
  const context = options.context ?? 'generic'
  const maxImages = options.maxImages ?? 5

  if (err instanceof ApiError) {
    const translated = translateErrorCode(err.code, err.params, t, maxImages)
    if (err.code === 'image_too_many') {
      return {
        title: contextTitle('submit', t),
        message: translated ?? t('report.errors.imageTooMany', { max: maxImages }),
      }
    }

    if (err.isNetworkError) {
      return {
        title: t('report.errors.networkErrorTitle'),
        message: t('report.errors.networkErrorMessage'),
      }
    }

    if (err.status >= 500) {
      return {
        title: t('report.errors.serverErrorTitle'),
        message: t('report.errors.serverErrorMessage'),
        detail: isUnhelpfulApiMessage(err.message) ? undefined : err.message,
      }
    }

    if (translated) {
      return {
        title: contextTitle(context, t),
        message: translated,
      }
    }

    const message = isUnhelpfulApiMessage(err.message)
      ? t('apiErrors.unknown')
      : err.message

    return {
      title: contextTitle(context, t),
      message,
    }
  }

  if (err instanceof Error) {
    return {
      title: contextTitle(context, t),
      message: err.message,
    }
  }

  return {
    title: contextTitle(context, t),
    message: t('apiErrors.unknown'),
  }
}

export function formatSubmitError(
  err: unknown,
  t: TranslateFn,
  maxImages: number,
): FormErrorDisplay {
  return formatApiError(err, t, { context: 'submit', maxImages })
}

export function translateSubmissionWarnings(
  warnings: SubmissionWarning[],
  t: TranslateFn,
): string[] {
  const seen = new Set<string>()
  const messages: string[] = []

  for (const warning of warnings) {
    if (seen.has(warning.code)) continue
    seen.add(warning.code)

    const key = WARNING_KEYS[warning.code]
    if (!key) continue

    messages.push(
      t(key, {
        meters: warning.params?.meters,
      }),
    )
  }

  return messages
}

/** @deprecated Use SubmissionWarning objects from the API */
export function normalizeSubmissionWarnings(raw: unknown): SubmissionWarning[] {
  if (!Array.isArray(raw)) return []
  return raw.flatMap((item) => {
    if (item && typeof item === 'object' && 'code' in item) {
      const warning = item as SubmissionWarning
      return [{ code: warning.code, params: warning.params }]
    }
    if (typeof item === 'string') {
      if (item.includes('admin will review') || item.includes('automated checks')) {
        return [{ code: 'pending_review' }]
      }
      if (item.includes('already registered within')) {
        const match = item.match(/within (\d+(?:\.\d+)?)m/)
        return [{ code: 'duplicate_nearby', params: { meters: match ? Number(match[1]) : 25 } }]
      }
    }
    return []
  })
}

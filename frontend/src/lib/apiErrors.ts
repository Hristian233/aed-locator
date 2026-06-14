import { ApiError } from './api'

export type FormErrorDisplay = {
  title?: string
  message: string
  detail?: string
}

type TranslateFn = (key: string, options?: Record<string, unknown>) => string

const UNHELPFUL_API_MESSAGES = [
  /^Request failed \(\d+\)$/,
  /^Internal [Ss]erver [Ee]rror$/,
  /^Bad gateway/,
  /^Service [Uu]navailable$/,
  /^Gateway [Tt]imeout$/,
]

export function isUnhelpfulApiMessage(message: string): boolean {
  const trimmed = message.trim()
  if (!trimmed) return true
  return UNHELPFUL_API_MESSAGES.some((pattern) => pattern.test(trimmed))
}

export function simpleFormError(message: string): FormErrorDisplay {
  return { message }
}

export function formatSubmitError(
  err: unknown,
  t: TranslateFn,
  maxImages: number,
): FormErrorDisplay {
  if (err instanceof ApiError) {
    if (err.code === 'image_too_many') {
      return {
        title: t('report.errors.submissionFailedTitle'),
        message: t('report.errors.imageTooMany', { max: err.maxImages ?? maxImages }),
      }
    }

    if (err.isNetworkError) {
      return {
        title: t('report.errors.networkErrorTitle'),
        message: t('report.errors.networkErrorMessage'),
      }
    }

    if (err.status >= 500) {
      const detail = isUnhelpfulApiMessage(err.message) ? undefined : err.message
      return {
        title: t('report.errors.serverErrorTitle'),
        message: t('report.errors.serverErrorMessage'),
        detail,
      }
    }

    const message = isUnhelpfulApiMessage(err.message)
      ? t('report.errors.submissionFailedMessage')
      : err.message

    return {
      title: t('report.errors.submissionFailedTitle'),
      message,
    }
  }

  if (err instanceof Error) {
    return {
      title: t('report.errors.submissionFailedTitle'),
      message: err.message,
    }
  }

  return {
    title: t('report.errors.submissionFailedTitle'),
    message: t('report.errors.submissionFailedMessage'),
  }
}

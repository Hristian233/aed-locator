import type { FormErrorDisplay } from '../lib/apiErrors'

export function FormErrorAlert({ title, message, detail }: FormErrorDisplay) {
  return (
    <div className="rounded-xl bg-red-50 p-3 text-sm text-red-900" role="alert">
      {title ? <p className="font-semibold">{title}</p> : null}
      <p className={title ? 'mt-1' : undefined}>{message}</p>
      {detail ? <p className="mt-1 text-red-800/80">{detail}</p> : null}
    </div>
  )
}

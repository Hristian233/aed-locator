import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export function SubmitPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [latitude, setLatitude] = useState<number | null>(null)
  const [longitude, setLongitude] = useState<number | null>(null)
  const [address, setAddress] = useState('')
  const [description, setDescription] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [warnings, setWarnings] = useState<string[]>([])

  const captureLocation = () => {
    if (!('geolocation' in navigator)) {
      setError('Geolocation is not supported on this device.')
      return
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLatitude(pos.coords.latitude)
        setLongitude(pos.coords.longitude)
        setError(null)
      },
      () => setError('Could not get your location. Enable location services.'),
      { enableHighAccuracy: true },
    )
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (latitude == null || longitude == null) {
      setError('Please capture your location first.')
      return
    }
    setLoading(true)
    setError(null)
    setWarnings([])
    try {
      const form = new FormData()
      form.append('latitude', String(latitude))
      form.append('longitude', String(longitude))
      if (address) form.append('address', address)
      if (description) form.append('description', description)
      if (image) form.append('image', image)

      const result = await api.submitAed(form)
      setWarnings(result.warnings)
      setTimeout(() => navigate('/'), 2500)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-lg flex-1 overflow-y-auto p-4 pb-12">
      <h1 className="text-2xl font-bold text-slate-900">Report an AED</h1>
      <p className="mt-1 text-sm text-slate-600">
        Help others in emergencies. Submissions are reviewed before appearing on the map.
      </p>

      {!user && (
        <p className="mt-4 rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
          <Link to="/auth" className="font-semibold underline">
            Sign in
          </Link>{' '}
          to track your submissions (optional — you can still report anonymously).
        </p>
      )}

      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <div>
          <button
            type="button"
            onClick={captureLocation}
            className="w-full rounded-xl border-2 border-dashed border-teal-300 bg-teal-50 py-4 text-sm font-semibold text-teal-800"
          >
            {latitude != null ? `Location: ${latitude.toFixed(5)}, ${longitude?.toFixed(5)}` : 'Use my current location'}
          </button>
        </div>

        <label className="block">
          <span className="text-sm font-medium text-slate-700">Address (optional)</span>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
            placeholder="e.g. Lobby near elevators"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-slate-700">Description</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm"
            placeholder="Floor, building name, access notes..."
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-slate-700">Photo of AED</span>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            capture="environment"
            onChange={(e) => setImage(e.target.files?.[0] ?? null)}
            className="mt-1 w-full text-sm"
          />
        </label>

        {error && <p className="text-sm text-red-600" role="alert">{error}</p>}
        {warnings.length > 0 && (
          <ul className="rounded-xl bg-amber-50 p-3 text-sm text-amber-900">
            {warnings.map((w) => (
              <li key={w}>• {w}</li>
            ))}
          </ul>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-xl bg-teal-600 py-3 font-semibold text-white disabled:opacity-60"
        >
          {loading ? 'Submitting…' : 'Submit for verification'}
        </button>
      </form>
    </div>
  )
}

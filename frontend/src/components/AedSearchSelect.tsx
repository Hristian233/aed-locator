import { useEffect, useId, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { aedMatchesSearch, formatAedOptionLabel } from '../lib/aedLabel'
import type { AED } from '../types'

type AedSearchSelectProps = {
  aeds: AED[]
  value: number | null
  onChange: (id: number | null) => void
  loading?: boolean
  loadError?: string | null
}

export function AedSearchSelect({
  aeds,
  value,
  onChange,
  loading = false,
  loadError = null,
}: AedSearchSelectProps) {
  const { t } = useTranslation()
  const listboxId = useId()
  const rootRef = useRef<HTMLDivElement>(null)
  const [open, setOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)

  const selectedAed = useMemo(
    () => (value == null ? null : aeds.find((aed) => aed.id === value) ?? null),
    [aeds, value],
  )

  const filteredAeds = useMemo(() => {
    const matches = aeds.filter((aed) => aedMatchesSearch(aed, searchQuery, t))
    return matches.sort((a, b) => a.id - b.id)
  }, [aeds, searchQuery, t])

  const options = useMemo(
    () => [{ id: null as number | null, aed: null as AED | null }, ...filteredAeds.map((aed) => ({ id: aed.id, aed }))],
    [filteredAeds],
  )

  useEffect(() => {
    if (!open) return

    const handlePointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    document.addEventListener('mousedown', handlePointerDown)
    return () => document.removeEventListener('mousedown', handlePointerDown)
  }, [open])

  useEffect(() => {
    setActiveIndex(0)
  }, [searchQuery, open])

  const displayValue = open
    ? searchQuery
    : selectedAed
      ? formatAedOptionLabel(selectedAed, t)
      : ''

  const selectOption = (id: number | null) => {
    onChange(id)
    setSearchQuery('')
    setOpen(false)
  }

  const handleInputChange = (nextQuery: string) => {
    setSearchQuery(nextQuery)
    if (!open) setOpen(true)
    if (value != null) onChange(null)
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      if (!open) setOpen(true)
      setActiveIndex((current) => Math.min(current + 1, options.length - 1))
      return
    }
    if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((current) => Math.max(current - 1, 0))
      return
    }
    if (event.key === 'Enter') {
      event.preventDefault()
      if (open && options[activeIndex]) {
        selectOption(options[activeIndex].id)
      }
      return
    }
    if (event.key === 'Escape') {
      event.preventDefault()
      setOpen(false)
      setSearchQuery('')
    }
  }

  return (
    <div ref={rootRef} className="relative">
      <input
        type="text"
        role="combobox"
        aria-expanded={open}
        aria-controls={listboxId}
        aria-autocomplete="list"
        aria-haspopup="listbox"
        value={displayValue}
        onChange={(event) => handleInputChange(event.target.value)}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKeyDown}
        disabled={loading || Boolean(loadError)}
        placeholder={t('report.relatedAedSearchPlaceholder')}
        className="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500"
      />

      {loading && (
        <p className="mt-1 text-xs text-slate-500">{t('report.relatedAedLoading')}</p>
      )}
      {loadError && (
        <p className="mt-1 text-xs text-red-600" role="alert">
          {loadError}
        </p>
      )}

      {open && !loading && !loadError && (
        <ul
          id={listboxId}
          role="listbox"
          className="absolute z-20 mt-1 max-h-56 w-full overflow-y-auto rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
        >
          {options.map((option, index) => {
            const isSelected = option.id === value
            const isActive = index === activeIndex
            const label =
              option.aed == null
                ? t('report.relatedAedNone')
                : formatAedOptionLabel(option.aed, t)

            return (
              <li
                key={option.id ?? 'none'}
                role="option"
                aria-selected={isSelected}
                className={`cursor-pointer px-3 py-2 text-sm ${
                  isActive ? 'bg-teal-50 text-teal-900' : 'text-slate-700'
                } ${isSelected ? 'font-medium' : ''}`}
                onMouseDown={(event) => event.preventDefault()}
                onMouseEnter={() => setActiveIndex(index)}
                onClick={() => selectOption(option.id)}
              >
                {label}
              </li>
            )
          })}
          {filteredAeds.length === 0 && searchQuery.trim() && (
            <li className="px-3 py-2 text-sm text-slate-500">{t('report.relatedAedNoResults')}</li>
          )}
        </ul>
      )}
    </div>
  )
}

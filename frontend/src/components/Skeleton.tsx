export function CardSkeleton() {
  return (
    <div className="space-y-3 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <div className="skeleton h-4 w-2/3" />
      <div className="skeleton h-3 w-full" />
      <div className="skeleton h-3 w-4/5" />
      <div className="skeleton h-10 w-full rounded-xl" />
    </div>
  )
}

export function MapSkeleton() {
  return <div className="skeleton h-full w-full" />
}

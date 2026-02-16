export function SkeletonKPI({ count = 4 }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton skeleton-kpi" style={{ flex: '1 1 45%', minWidth: 120 }} />
      ))}
    </div>
  )
}

export function SkeletonChart() {
  return <div className="skeleton skeleton-chart" />
}

export function SkeletonBars({ count = 5 }) {
  return (
    <div style={{ padding: '8px 0' }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="skeleton skeleton-bar" />
      ))}
    </div>
  )
}

export function ErrorBanner({ message }) {
  return (
    <div style={{
      padding: '12px 16px',
      background: 'var(--semantic-negative-bg, #FFF1F0)',
      border: '1px solid var(--semantic-negative)',
      borderRadius: 8,
      color: 'var(--semantic-negative)',
      fontSize: 13,
      marginBottom: 12,
    }}>
      <strong>Error al cargar datos</strong>
      {message && <div style={{ fontSize: 11, marginTop: 4, opacity: 0.8 }}>{message}</div>}
    </div>
  )
}

export function exportCSV(rows, filename) {
  if (!rows?.length) return
  const keys = Object.keys(rows[0])
  const csv = [
    keys.join(','),
    ...rows.map((r) => keys.map((k) => {
      const v = r[k]
      if (v == null) return ''
      const s = String(v)
      return s.includes(',') || s.includes('"') || s.includes('\n') ? `"${s.replace(/"/g, '""')}"` : s
    }).join(',')),
  ].join('\n')
  const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function ExportCSVButton({ rows, filename }) {
  if (!rows?.length) return null
  return (
    <button
      onClick={() => exportCSV(rows, filename)}
      style={{
        background: 'var(--bg-tertiary)',
        border: '1px solid var(--border)',
        borderRadius: 4,
        padding: '3px 8px',
        fontSize: 10,
        color: 'var(--text-secondary)',
        cursor: 'pointer',
        fontFamily: 'inherit',
      }}
    >
      CSV
    </button>
  )
}

export function SkeletonTab() {
  return (
    <div style={{ padding: 4 }}>
      <div className="skeleton" style={{ width: '40%', height: 16, marginBottom: 16 }} />
      <SkeletonKPI count={4} />
      <div style={{ marginTop: 16 }}>
        <div className="skeleton" style={{ width: '55%', height: 12, marginBottom: 10 }} />
        <SkeletonChart />
      </div>
      <div style={{ marginTop: 12 }}>
        <div className="skeleton" style={{ width: '45%', height: 12, marginBottom: 10 }} />
        <SkeletonBars count={4} />
      </div>
    </div>
  )
}

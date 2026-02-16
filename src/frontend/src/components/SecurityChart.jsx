import { useState, useEffect } from 'react'
import { useStore } from '../store'
import { SkeletonTab, ErrorBanner, ExportCSVButton } from './Skeleton'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts'

const COLORS = {
  'Homicidios': '#F5222D',
  'Hurtos': '#0050B3',
  'Delitos Sexuales': '#FA8C16',
  'Violencia Intrafamiliar': '#1890FF',
}

const RANGE_STYLE = {
  background: 'var(--bg-tertiary)',
  color: 'var(--text-primary)',
  border: '1px solid var(--border)',
  borderRadius: 4,
  padding: '2px 6px',
  fontSize: 11,
  outline: 'none',
  fontFamily: 'inherit',
}

export default function SecurityChart() {
  const { securityMatrix, fetchSecurityMatrix, errors } = useStore()
  const [yearRange, setYearRange] = useState(null)

  useEffect(() => { fetchSecurityMatrix() }, [])

  if (errors.seguridad) return <ErrorBanner message={errors.seguridad} />
  if (!securityMatrix) return <SkeletonTab />

  const allYears = [...new Set(securityMatrix.map((d) => d.anio))].sort()
  const minY = yearRange?.[0] ?? allYears[0]
  const maxY = yearRange?.[1] ?? allYears[allYears.length - 1]
  const years = allYears.filter((y) => y >= minY && y <= maxY)

  const pivoted = years.map((y) => {
    const row = { anio: y }
    securityMatrix.filter((d) => d.anio === y).forEach((d) => {
      row[d.tipo] = d.total
    })
    return row
  })

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <h3 className="section-title" style={{ marginBottom: 0 }}>Delitos por Ano</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <select value={minY} onChange={(e) => setYearRange([+e.target.value, maxY])} style={RANGE_STYLE}>
            {allYears.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
          <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>—</span>
          <select value={maxY} onChange={(e) => setYearRange([minY, +e.target.value])} style={RANGE_STYLE}>
            {allYears.filter((y) => y >= minY).map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={pivoted}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
          <XAxis dataKey="anio" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
          <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
          <Tooltip
            contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: 'var(--text-primary)', fontWeight: 600 }}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {Object.entries(COLORS).map(([key, color]) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              stroke={color}
              fill={color}
              fillOpacity={0.12}
              strokeWidth={2}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
        <div className="data-source">Fuente: Policia Nacional — datos.gov.co</div>
        <ExportCSVButton rows={pivoted} filename={`seguridad_${minY}-${maxY}.csv`} />
      </div>
    </div>
  )
}

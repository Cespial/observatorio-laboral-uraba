import { useState, useEffect } from 'react'
import { useStore } from '../store'
import { SkeletonTab, ErrorBanner, ExportCSVButton } from './Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts'

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

export default function IcfesChart() {
  const { icfesData, fetchIcfes, errors } = useStore()
  const [periodRange, setPeriodRange] = useState(null)

  useEffect(() => { fetchIcfes() }, [])

  if (errors.educacion) return <ErrorBanner message={errors.educacion} />
  if (!icfesData) return <SkeletonTab />

  const allData = icfesData
    .filter((d) => d.prom_global !== null)
    .map((d) => ({
      periodo: d.periodo,
      global: Math.round(d.prom_global),
      matematicas: Math.round(d.prom_matematicas || 0),
      estudiantes: d.estudiantes,
    }))

  const allPeriods = allData.map((d) => d.periodo)
  const minP = periodRange?.[0] ?? allPeriods[0]
  const maxP = periodRange?.[1] ?? allPeriods[allPeriods.length - 1]
  const data = allData.filter((d) => d.periodo >= minP && d.periodo <= maxP)

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <h3 className="section-title" style={{ marginBottom: 0 }}>ICFES Saber 11</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <select value={minP} onChange={(e) => setPeriodRange([e.target.value, maxP])} style={RANGE_STYLE}>
            {allPeriods.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
          <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>—</span>
          <select value={maxP} onChange={(e) => setPeriodRange([minP, e.target.value])} style={RANGE_STYLE}>
            {allPeriods.filter((p) => p >= minP).map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
          <XAxis dataKey="periodo" tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} angle={-45} textAnchor="end" height={50} />
          <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} domain={[0, 300]} />
          <Tooltip
            contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: 'var(--text-primary)', fontWeight: 600 }}
          />
          <Bar dataKey="global" fill="#0050B3" opacity={0.9} radius={[4, 4, 0, 0]} name="Global" />
          <Bar dataKey="matematicas" fill="#40A9FF" opacity={0.8} radius={[4, 4, 0, 0]} name="Matematicas" />
        </BarChart>
      </ResponsiveContainer>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
        <div className="data-source">Fuente: ICFES Saber 11 — datos.gov.co</div>
        <ExportCSVButton rows={data} filename={`icfes_${minP}-${maxP}.csv`} />
      </div>
    </div>
  )
}

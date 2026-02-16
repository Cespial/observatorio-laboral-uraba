import { useEffect } from 'react'
import { useStore } from '../store'
import { SkeletonTab, ErrorBanner, ExportCSVButton } from './Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'

const COLORS = ['#0050B3', '#1890FF', '#40A9FF', '#69C0FF', '#91D5FF', '#B7DCFF', '#D6EBFF', '#E6F4FF']

export default function VictimasChart() {
  const { victimasData, fetchVictimas, errors } = useStore()

  useEffect(() => { fetchVictimas() }, [])

  if (errors.victimas) return <ErrorBanner message={errors.victimas} />
  if (!victimasData) return <SkeletonTab />

  const data = victimasData
    .filter((d) => d.personas > 0)
    .slice(0, 8)
    .map((d) => ({
      hecho: d.dimension?.length > 25 ? d.dimension.slice(0, 25) + '...' : d.dimension,
      full: d.dimension,
      personas: d.personas,
    }))

  return (
    <div className="fade-in">
      <h3 className="section-title">Victimas por Hecho Victimizante</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} layout="vertical" margin={{ left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
          <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
          <YAxis dataKey="hecho" type="category" tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} width={140} />
          <Tooltip
            contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
            formatter={(v) => [v.toLocaleString('es-CO'), 'Personas']}
            labelFormatter={(l, payload) => payload?.[0]?.payload?.full || l}
          />
          <Bar dataKey="personas" radius={[0, 4, 4, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 4 }}>
        <div className="data-source">Fuente: Unidad para las Victimas — datos.gov.co</div>
        <ExportCSVButton rows={data} filename="victimas_hechos.csv" />
      </div>
    </div>
  )
}

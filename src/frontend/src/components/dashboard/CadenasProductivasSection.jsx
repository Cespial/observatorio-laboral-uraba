import DashboardCard from './DashboardCard'
import { ExportCSVButton } from '../Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Treemap,
} from 'recharts'

const CADENA_COLORS = {
  'Banano y Plátano': '#52C41A',
  'Ganadería y Lácteos': '#FA8C16',
  'Turismo y Gastronomía': '#13C2C2',
  'Comercio y Logística Portuaria': '#1890FF',
  'Construcción e Infraestructura': '#F5222D',
  'Servicios y Administrativo': '#722ED1',
}

const tooltipStyle = {
  background: 'var(--bg-card)', border: '1px solid var(--border)',
  borderRadius: 6, fontSize: 12,
}

function fmt(val) {
  if (val == null) return '---'
  if (typeof val === 'number') return val.toLocaleString('es-CO')
  return String(val)
}

function fmtSalary(val) {
  if (val == null) return '---'
  return `$${(val / 1000000).toFixed(1)}M`
}

export default function CadenasProductivasSection({ data }) {
  if (!data?.length) return null

  const treemapData = data.map(c => ({
    name: c.cadena,
    size: c.ofertas,
    color: CADENA_COLORS[c.cadena] || '#8E94A9',
  }))

  return (
    <>
      <DashboardCard span={2} title="Cadenas Productivas de Uraba">
        {/* Stacked horizontal bars by chain */}
        <ResponsiveContainer width="100%" height={Math.max(180, data.length * 36)}>
          <BarChart data={data} layout="vertical" margin={{ left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
            <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
            <YAxis
              dataKey="cadena" type="category"
              tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} width={140}
              tickFormatter={(v) => v.length > 22 ? v.slice(0, 22) + '...' : v}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(v, name, props) => {
                const p = props?.payload
                return [
                  `${v} ofertas | ${p?.empresas || 0} empresas | ${p?.salario_promedio ? fmtSalary(p.salario_promedio) : 'N/A'}`,
                  'Cadena'
                ]
              }}
              labelFormatter={(l, p) => p?.[0]?.payload?.cadena || l}
            />
            <Bar dataKey="ofertas" radius={[0, 4, 4, 0]}>
              {data.map((c, i) => (
                <Cell key={i} fill={CADENA_COLORS[c.cadena] || '#8E94A9'} fillOpacity={0.85} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Summary cards per chain */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6, marginTop: 12 }}>
          {data.slice(0, 6).map(c => (
            <div key={c.cadena} style={{
              background: 'var(--bg-secondary)', borderRadius: 8, padding: '8px 10px',
              border: '1px solid var(--border)', borderLeft: `3px solid ${CADENA_COLORS[c.cadena] || '#8E94A9'}`,
            }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {c.cadena}
              </div>
              <div style={{ display: 'flex', gap: 8, fontSize: 10, color: 'var(--text-secondary)' }}>
                <span><strong style={{ color: 'var(--accent-primary)' }}>{fmt(c.ofertas)}</strong> ofertas</span>
                <span>{fmt(c.empresas)} emp.</span>
              </div>
              {c.salario_promedio && (
                <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>
                  Salario prom: {fmtSalary(c.salario_promedio)}
                </div>
              )}
            </div>
          ))}
        </div>
      </DashboardCard>

      {/* Top Skills por Cadena */}
      <DashboardCard title="Skills por Cadena Productiva" actions={
        <ExportCSVButton
          rows={data.flatMap(c => c.top_skills.map(s => ({ cadena: c.cadena, ...s })))}
          filename="cadenas_skills.csv"
        />
      }>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {data.filter(c => c.top_skills?.length > 0).slice(0, 4).map(c => (
            <div key={c.cadena}>
              <div style={{
                fontSize: 10, fontWeight: 600, color: CADENA_COLORS[c.cadena] || 'var(--text-primary)',
                marginBottom: 4, textTransform: 'uppercase',
              }}>
                {c.cadena}
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                {c.top_skills.slice(0, 6).map((s, i) => (
                  <span key={s.skill} style={{
                    padding: '2px 8px', borderRadius: 10, fontSize: 10,
                    background: i < 2 ? (CADENA_COLORS[c.cadena] || 'var(--accent-primary)') : 'var(--bg-tertiary)',
                    color: i < 2 ? '#fff' : 'var(--text-secondary)',
                    border: i >= 2 ? '1px solid var(--border)' : 'none',
                  }}>
                    {s.skill} ({s.demanda})
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </DashboardCard>
    </>
  )
}

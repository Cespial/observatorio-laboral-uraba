import DashboardCard from './DashboardCard'
import { ExportCSVButton } from '../Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts'

const tooltipStyle = {
  background: 'var(--bg-card)', border: '1px solid var(--border)',
  borderRadius: 6, fontSize: 12,
}

function getSemaforoColor(value) {
  if (value == null) return 'var(--text-muted)'
  if (value >= 70) return '#F5222D'
  if (value >= 50) return '#FA8C16'
  if (value >= 30) return '#FAAD14'
  return '#52C41A'
}

function SemaforoBadge({ value, label }) {
  const color = getSemaforoColor(value)
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '6px 10px', background: 'var(--bg-secondary)',
      borderRadius: 6, border: '1px solid var(--border)',
    }}>
      <div style={{
        width: 10, height: 10, borderRadius: '50%',
        background: color, flexShrink: 0,
      }} />
      <div>
        <div style={{ fontSize: 14, fontWeight: 700, color }}>
          {value != null ? `${value}%` : '---'}
        </div>
        <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>{label}</div>
      </div>
    </div>
  )
}

export default function InformalidadSection({ data }) {
  if (!data?.length) return null

  // Ranking by composite index
  const ranked = data.filter(d => d.indice_compuesto != null)

  return (
    <>
      <DashboardCard span={2} title="Informalidad Laboral" subtitle="Indice compuesto por municipio">
        {/* Horizontal bar ranking */}
        <ResponsiveContainer width="100%" height={Math.max(180, ranked.length * 32)}>
          <BarChart data={ranked} layout="vertical" margin={{ left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
            <XAxis type="number" domain={[0, 100]} tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} unit="%" />
            <YAxis
              dataKey="municipio" type="category"
              tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} width={100}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(v, name, props) => {
                const p = props?.payload
                return [
                  `Compuesto: ${v}% | IPM: ${p?.tasa_ipm ?? 'N/A'}% | Proxy: ${p?.proxy_informal_pct ?? 'N/A'}% | Pobreza: ${p?.pobreza_monetaria ?? 'N/A'}%`,
                  'Informalidad'
                ]
              }}
            />
            <Bar dataKey="indice_compuesto" radius={[0, 4, 4, 0]}>
              {ranked.map((d, i) => (
                <Cell key={i} fill={getSemaforoColor(d.indice_compuesto)} fillOpacity={0.85} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </DashboardCard>

      {/* Detail cards */}
      <DashboardCard title="Detalle Informalidad" actions={<ExportCSVButton rows={data} filename="informalidad.csv" />}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {ranked.slice(0, 6).map(d => (
            <div key={d.dane_code} style={{
              background: 'var(--bg-secondary)', borderRadius: 8, padding: '8px 10px',
              border: '1px solid var(--border)',
              borderLeft: `3px solid ${getSemaforoColor(d.indice_compuesto)}`,
            }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                {d.municipio}
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 4 }}>
                <SemaforoBadge value={d.tasa_ipm} label="IPM Informal" />
                <SemaforoBadge value={d.proxy_informal_pct} label="Proxy Ofertas" />
                <SemaforoBadge value={d.pobreza_monetaria} label="Pobreza Mon." />
              </div>
              <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 4 }}>
                Contratos: {d.contratos_indefinido} indef. vs {d.contratos_no_indefinido} no-indef.
                ({d.ofertas_con_contrato} con tipo)
              </div>
            </div>
          ))}
        </div>
      </DashboardCard>
    </>
  )
}

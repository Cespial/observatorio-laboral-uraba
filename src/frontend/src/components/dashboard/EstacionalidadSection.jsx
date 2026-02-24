import DashboardCard from './DashboardCard'
import { ExportCSVButton } from '../Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, LineChart, Line, Legend,
} from 'recharts'

const MES_LABELS = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

const CLASE_COLORS = {
  pico: '#52C41A',
  normal: '#1890FF',
  valle: '#F5222D',
}

const tooltipStyle = {
  background: 'var(--bg-card)', border: '1px solid var(--border)',
  borderRadius: 6, fontSize: 12,
}

export default function EstacionalidadSection({ data }) {
  if (!data) return null
  const { perfil_general, sectores_estacionales, promedio_mensual } = data

  if (!perfil_general?.length) return null

  return (
    <>
      {/* General monthly profile */}
      <DashboardCard span={2} title="Estacionalidad Laboral" subtitle={`Promedio mensual: ${promedio_mensual} ofertas`}>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={perfil_general} margin={{ left: 0, right: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
            <XAxis dataKey="mes_nombre" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
            <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(v, name, props) => {
                const p = props?.payload
                if (name === 'ofertas') {
                  return [`${v} ofertas (${p?.clasificacion || 'normal'})`, 'Ofertas']
                }
                return [v, name]
              }}
            />
            <Bar dataKey="ofertas" radius={[4, 4, 0, 0]}>
              {perfil_general.map((entry, i) => (
                <Cell key={i} fill={CLASE_COLORS[entry.clasificacion] || '#1890FF'} fillOpacity={0.85} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Badges for peaks and valleys */}
        <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
          {perfil_general.filter(m => m.clasificacion === 'pico').map(m => (
            <span key={m.mes} style={{
              padding: '3px 10px', borderRadius: 12, fontSize: 10, fontWeight: 600,
              background: '#F6FFED', color: '#52C41A', border: '1px solid #B7EB8F',
            }}>
              Pico: {m.mes_nombre} ({m.ofertas})
            </span>
          ))}
          {perfil_general.filter(m => m.clasificacion === 'valle').map(m => (
            <span key={m.mes} style={{
              padding: '3px 10px', borderRadius: 12, fontSize: 10, fontWeight: 600,
              background: '#FFF1F0', color: '#F5222D', border: '1px solid #FFA39E',
            }}>
              Valle: {m.mes_nombre} ({m.ofertas})
            </span>
          ))}
        </div>
      </DashboardCard>

      {/* Sector × Month Heatmap */}
      {sectores_estacionales?.length > 0 && (
        <DashboardCard
          span={2}
          title="Heatmap Sectorial por Mes"
          actions={<ExportCSVButton rows={sectores_estacionales} filename="estacionalidad_sectores.csv" />}
        >
          <div style={{ overflowX: 'auto' }}>
            <table style={{
              width: '100%', borderCollapse: 'collapse', fontSize: 10,
            }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', padding: '4px 6px', color: 'var(--text-secondary)', fontWeight: 600 }}>Sector</th>
                  {MES_LABELS.map(m => (
                    <th key={m} style={{ padding: '4px 4px', color: 'var(--text-muted)', fontWeight: 500, textAlign: 'center', minWidth: 32 }}>{m}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sectores_estacionales.slice(0, 10).map(row => {
                  const maxVal = Math.max(...MES_LABELS.map(m => row[m] || 0), 1)
                  return (
                    <tr key={row.sector}>
                      <td style={{
                        padding: '4px 6px', color: 'var(--text-primary)', fontWeight: 500,
                        maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}>
                        {row.sector}
                      </td>
                      {MES_LABELS.map(m => {
                        const val = row[m] || 0
                        const intensity = val / maxVal
                        const bg = val === 0 ? 'var(--bg-secondary)'
                          : `rgba(0, 80, 179, ${0.1 + intensity * 0.8})`
                        const color = intensity > 0.5 ? '#fff' : 'var(--text-secondary)'
                        return (
                          <td key={m} style={{
                            padding: '4px 4px', textAlign: 'center',
                            background: bg, color, borderRadius: 2,
                          }}>
                            {val > 0 ? val : ''}
                          </td>
                        )
                      })}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Peak/valley badges per sector */}
          <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
            {sectores_estacionales.slice(0, 5).filter(s => s.picos?.length > 0 || s.valles?.length > 0).map(s => (
              <div key={s.sector} style={{ fontSize: 10, color: 'var(--text-secondary)', display: 'flex', gap: 6, alignItems: 'center' }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)', minWidth: 90 }}>
                  {s.sector.length > 16 ? s.sector.slice(0, 16) + '...' : s.sector}
                </span>
                {s.picos?.length > 0 && (
                  <span style={{ color: '#52C41A' }}>
                    Picos: {s.picos.map(m => MES_LABELS[m - 1]).join(', ')}
                  </span>
                )}
                {s.valles?.length > 0 && (
                  <span style={{ color: '#F5222D' }}>
                    Valles: {s.valles.map(m => MES_LABELS[m - 1]).join(', ')}
                  </span>
                )}
              </div>
            ))}
          </div>
        </DashboardCard>
      )}
    </>
  )
}

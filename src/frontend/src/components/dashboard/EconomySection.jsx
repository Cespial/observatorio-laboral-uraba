import DashboardCard from './DashboardCard'
import { ExportCSVButton } from '../Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area, Cell,
} from 'recharts'

const COLORS = ['#0050B3', '#1890FF', '#40A9FF', '#69C0FF', '#52C41A', '#FA8C16', '#F5222D', '#8E94A9']

const tooltipStyle = {
  background: 'var(--bg-card)', border: '1px solid var(--border)',
  borderRadius: 6, fontSize: 12,
}

function fmt(val) {
  if (val == null) return '---'
  if (typeof val === 'number') return val.toLocaleString('es-CO')
  return String(val)
}

export default function EconomySection({ economiaData, summary }) {
  if (!economiaData) return null

  const { internet, secop, terridata_economia } = economiaData

  // PIB per capita from terridata
  const pibRow = terridata_economia?.find(r =>
    r.indicador?.toLowerCase().includes('pib') && r.indicador?.toLowerCase().includes('capita')
  )
  const pibPerCapita = pibRow?.dato_numerico

  // Total negocios from summary
  const negocios = summary?.google_places

  // Internet accesos (last data point)
  const lastInet = internet?.length ? internet[internet.length - 1] : null

  // Inversion publica top items
  const secopTop = secop
    ?.filter(r => r.indicador && r.valor != null)
    .slice(0, 6)
    .map(r => ({
      tipo: r.indicador?.length > 30 ? r.indicador.slice(0, 30) + '...' : r.indicador,
      full: r.indicador,
      valor: r.valor,
      anio: r.anio,
    })) || []

  // Economy indicators
  const econIndicators = terridata_economia
    ?.filter(r => r.dato_numerico != null)
    .sort((a, b) => b.dato_numerico - a.dato_numerico)
    .slice(0, 8)
    .map(r => ({
      indicador: r.indicador?.length > 28 ? r.indicador.slice(0, 28) + '...' : r.indicador,
      full: r.indicador,
      valor: r.dato_numerico,
      anio: r.anio,
    })) || []

  return (
    <>
      {/* KPI Row */}
      <DashboardCard title="Economia">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '10px 12px', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--accent-primary)' }}>
              {pibPerCapita ? `$${fmt(Math.round(pibPerCapita / 1000))}K` : '---'}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>PIB per capita</div>
          </div>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '10px 12px', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
              {negocios != null ? fmt(negocios) : '---'}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Negocios mapeados</div>
          </div>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '10px 12px', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
              {lastInet?.total_accesos ? fmt(lastInet.total_accesos) : '---'}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Accesos internet</div>
          </div>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '10px 12px', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
              {secopTop.length > 0 ? fmt(secopTop.length) : '---'}
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Inv. publica items</div>
          </div>
        </div>
      </DashboardCard>

      {/* Economia Indicators */}
      {econIndicators.length > 0 && (
        <DashboardCard title="Indicadores Economicos" actions={<ExportCSVButton rows={econIndicators} filename="dashboard_economia_indicadores.csv" />}>
          <ResponsiveContainer width="100%" height={Math.max(160, econIndicators.length * 24)}>
            <BarChart data={econIndicators} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <YAxis dataKey="indicador" type="category" tick={{ fill: 'var(--text-secondary)', fontSize: 8 }} width={130} />
              <Tooltip contentStyle={tooltipStyle}
                formatter={(v) => [typeof v === 'number' ? v.toLocaleString('es-CO') : v, 'Valor']}
                labelFormatter={(l, p) => p?.[0]?.payload?.full || l}
              />
              <Bar dataKey="valor" radius={[0, 4, 4, 0]}>
                {econIndicators.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </DashboardCard>
      )}

      {/* Internet Fijo */}
      {internet?.length > 0 && (
        <DashboardCard title="Internet Fijo" subtitle="MinTIC" actions={<ExportCSVButton rows={internet} filename="dashboard_internet.csv" />}>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={internet}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis dataKey="anio" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <Tooltip contentStyle={tooltipStyle}
                formatter={(v) => [v.toLocaleString('es-CO'), 'Accesos']}
              />
              <Area type="monotone" dataKey="total_accesos" stroke="#0050B3" fill="#0050B3" fillOpacity={0.15} strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </DashboardCard>
      )}

      {/* Inversion Publica */}
      {secopTop.length > 0 && (
        <DashboardCard title="Inversion Publica" subtitle="DNP TerriData" actions={<ExportCSVButton rows={secopTop} filename="dashboard_inversion.csv" />}>
          <ResponsiveContainer width="100%" height={Math.max(140, secopTop.length * 26)}>
            <BarChart data={secopTop} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <YAxis dataKey="tipo" type="category" tick={{ fill: 'var(--text-secondary)', fontSize: 8 }} width={130} />
              <Tooltip contentStyle={tooltipStyle}
                formatter={(v) => [typeof v === 'number' ? v.toLocaleString('es-CO') : v, 'Valor']}
                labelFormatter={(l, p) => p?.[0]?.payload?.full || l}
              />
              <Bar dataKey="valor" fill="#0050B3" opacity={0.85} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </DashboardCard>
      )}
    </>
  )
}

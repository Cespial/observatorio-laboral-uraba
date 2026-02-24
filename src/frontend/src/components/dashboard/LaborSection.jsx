import DashboardCard from './DashboardCard'
import { ExportCSVButton } from '../Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area, Cell, PieChart, Pie,
  LineChart, Line, Legend,
} from 'recharts'

const COLORS = [
  '#0050B3', '#1890FF', '#40A9FF', '#69C0FF', '#52C41A',
  '#FA8C16', '#F5222D', '#8E94A9', '#722ED1', '#13C2C2',
]

const RANGO_COLORS = {
  '< SMMLV': '#F5222D',
  '1-2 SMMLV': '#FA8C16',
  '2-3 SMMLV': '#FAAD14',
  '3-5 SMMLV': '#52C41A',
  '> 5 SMMLV': '#0050B3',
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

/** Inline mini sparkline SVG from serie data */
function MiniSparkline({ data, dataKey, color = '#0050B3' }) {
  if (!data?.length || data.length < 2) return null
  const vals = data.map(d => d[dataKey] || 0)
  const max = Math.max(...vals, 1)
  const min = Math.min(...vals, 0)
  const range = max - min || 1
  const w = 60
  const h = 20
  const points = vals.map((v, i) =>
    `${(i / (vals.length - 1)) * w},${h - ((v - min) / range) * h}`
  ).join(' ')
  return (
    <svg width={w} height={h} style={{ display: 'block', marginTop: 4 }}>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}

/** Trend badge comparing last two periods */
function TrendBadge({ data, dataKey }) {
  if (!data?.length || data.length < 2) return null
  const curr = data[data.length - 1]?.[dataKey] || 0
  const prev = data[data.length - 2]?.[dataKey] || 0
  if (prev === 0) return null
  const pct = Math.round(((curr - prev) / prev) * 100)
  const isUp = pct >= 0
  const color = isUp ? 'var(--semantic-positive)' : 'var(--semantic-negative)'
  return (
    <span style={{ fontSize: 10, fontWeight: 600, color, marginLeft: 6 }}>
      {isUp ? '\u2191' : '\u2193'} {Math.abs(pct)}%
    </span>
  )
}

export default function LaborSection({ empleoData, empleoKpis, empleoAnalytics, salarioImputado }) {
  const kpis = empleoKpis
  const stats = empleoData?.stats
  const serie = empleoData?.serie
  const skills = empleoData?.skills
  const salarios = empleoData?.salarios
  const sectores = empleoData?.sectores
  const dinamismo = empleoAnalytics?.dinamismo
  const termometro = empleoAnalytics?.termometro

  // Derive extra KPIs
  const topFuente = stats?.por_fuente?.[0]
  const ultimos7 = termometro?.reduce((s, m) => s + (m.ultimos_7_dias || 0), 0)

  return (
    <>
      {/* KPI Row */}
      <DashboardCard span={2} title="Mercado Laboral">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '12px 14px', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--accent-primary)' }}>
                {fmt(kpis?.total_ofertas ?? stats?.total_ofertas)}
              </div>
              <TrendBadge data={serie} dataKey="ofertas" />
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Ofertas totales</div>
            <MiniSparkline data={serie} dataKey="ofertas" color="#0050B3" />
          </div>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '12px 14px', border: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>
                {fmt(kpis?.total_empresas)}
              </div>
              <TrendBadge data={serie} dataKey="empresas" />
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Empresas contratando</div>
            <MiniSparkline data={serie} dataKey="empresas" color="#52C41A" />
          </div>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '12px 14px', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--text-primary)' }}>
              {kpis?.salario_promedio ? fmtSalary(kpis.salario_promedio) : '---'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Salario promedio</div>
            {salarioImputado?.cobertura && (
              <div style={{
                marginTop: 4, padding: '2px 8px', borderRadius: 10, fontSize: 9,
                background: 'var(--bg-tertiary)', color: 'var(--text-muted)',
                display: 'inline-block', border: '1px solid var(--border)',
              }}>
                {salarioImputado.cobertura.pct_salario_real}% real
                {salarioImputado.cobertura.pct_cobertura_total > salarioImputado.cobertura.pct_salario_real && (
                  <> + {(salarioImputado.cobertura.pct_cobertura_total - salarioImputado.cobertura.pct_salario_real).toFixed(1)}% estimado</>
                )}
              </div>
            )}
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginTop: 10 }}>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '12px 14px', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {kpis?.sector_top || '---'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Sector top</div>
          </div>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '12px 14px', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {topFuente ? `${topFuente.fuente} (${topFuente.total})` : '---'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Top fuente</div>
          </div>
          <div style={{ background: 'var(--bg-secondary)', borderRadius: 8, padding: '12px 14px', border: '1px solid var(--border)' }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: ultimos7 > 0 ? 'var(--semantic-positive)' : 'var(--text-muted)' }}>
              {ultimos7 != null ? fmt(ultimos7) : '---'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Ultimos 7 dias</div>
          </div>
        </div>
      </DashboardCard>

      {/* Ofertas por Mes */}
      {serie?.length > 0 && (
        <DashboardCard title="Ofertas por Mes" actions={<ExportCSVButton rows={serie} filename="dashboard_serie_temporal.csv" />}>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={serie}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis dataKey="periodo" tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} angle={-45} textAnchor="end" height={45} />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area type="monotone" dataKey="ofertas" stroke="#0050B3" fill="#0050B3" fillOpacity={0.15} strokeWidth={2} name="Ofertas" />
              <Area type="monotone" dataKey="empresas" stroke="#52C41A" fill="#52C41A" fillOpacity={0.1} strokeWidth={1.5} name="Empresas" />
            </AreaChart>
          </ResponsiveContainer>
        </DashboardCard>
      )}

      {/* Top Sectores */}
      {sectores?.length > 0 && (
        <DashboardCard title="Top Sectores" actions={<ExportCSVButton rows={sectores} filename="dashboard_sectores.csv" />}>
          <ResponsiveContainer width="100%" height={Math.max(180, Math.min(sectores.length, 10) * 24)}>
            <BarChart data={sectores.slice(0, 10)} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <YAxis
                dataKey="sector" type="category"
                tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} width={120}
                tickFormatter={(v) => v.length > 20 ? v.slice(0, 20) + '...' : v}
              />
              <Tooltip contentStyle={tooltipStyle}
                formatter={(v) => [v, 'Ofertas']}
                labelFormatter={(l, p) => p?.[0]?.payload?.sector || l}
              />
              <Bar dataKey="ofertas" radius={[0, 4, 4, 0]}>
                {sectores.slice(0, 10).map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </DashboardCard>
      )}

      {/* Distribucion Salarial */}
      {salarios?.rangos?.length > 0 && (
        <DashboardCard title="Distribucion Salarial" actions={<ExportCSVButton rows={salarios.rangos} filename="dashboard_salarios.csv" />}>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={salarios.rangos} dataKey="ofertas" nameKey="rango"
                cx="50%" cy="50%" outerRadius={80}
                label={({ rango, ofertas }) => `${rango}: ${ofertas}`}
                labelLine={{ stroke: 'var(--text-muted)', strokeWidth: 1 }}
              >
                {salarios.rangos.map((entry, i) => (
                  <Cell key={entry.rango} fill={RANGO_COLORS[entry.rango] || COLORS[i % COLORS.length]} fillOpacity={0.85} />
                ))}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
            </PieChart>
          </ResponsiveContainer>
        </DashboardCard>
      )}

      {/* Skills Demandadas */}
      {skills?.length > 0 && (
        <DashboardCard title="Skills Demandadas" actions={<ExportCSVButton rows={skills} filename="dashboard_skills.csv" />}>
          <ResponsiveContainer width="100%" height={Math.min(skills.length, 10) * 24 + 20}>
            <BarChart data={skills.slice(0, 10)} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <YAxis dataKey="skill" type="category" tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} width={100} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => [v, 'Demanda']} />
              <Bar dataKey="demanda" radius={[0, 4, 4, 0]}>
                {skills.slice(0, 10).map((_, i) => (
                  <Cell key={i} fill={i < 3 ? '#0050B3' : '#69C0FF'} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </DashboardCard>
      )}

      {/* Dinamismo Laboral */}
      {dinamismo?.length > 0 && (
        <DashboardCard title="Dinamismo Laboral" actions={<ExportCSVButton rows={dinamismo} filename="dashboard_dinamismo.csv" />}>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={dinamismo}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis dataKey="mes" tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} angle={-45} textAnchor="end" height={45} />
              <YAxis yAxisId="left" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} unit="%" />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Line yAxisId="left" type="monotone" dataKey="ofertas" stroke="#0050B3" strokeWidth={2} dot={{ r: 3 }} name="Ofertas" />
              <Line yAxisId="right" type="monotone" dataKey="crecimiento_pct" stroke="#52C41A" strokeWidth={1.5} strokeDasharray="4 2" dot={false} name="Crecimiento %" connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </DashboardCard>
      )}

      {/* Top Empleadores */}
      {stats?.top_empresas?.length > 0 && (
        <DashboardCard title="Top Empleadores" actions={<ExportCSVButton rows={stats.top_empresas} filename="dashboard_empleadores.csv" />}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {stats.top_empresas.slice(0, 10).map((e, i) => (
              <div key={i} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '6px 10px', background: 'var(--bg-secondary)', borderRadius: 6,
                border: '1px solid var(--border)',
              }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: 12 }}>
                  <span style={{ color: 'var(--text-muted)', marginRight: 6, fontWeight: 700 }}>#{i + 1}</span>
                  {e.empresa}
                </span>
                <span style={{ color: 'var(--accent-primary)', fontSize: 13, fontWeight: 600 }}>
                  {e.total}
                </span>
              </div>
            ))}
          </div>
        </DashboardCard>
      )}
    </>
  )
}

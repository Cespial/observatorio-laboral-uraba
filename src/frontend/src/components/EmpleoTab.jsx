import { useEffect } from 'react'
import { useStore } from '../store'
import { SkeletonTab, ErrorBanner, ExportCSVButton } from './Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area, Cell, PieChart, Pie,
} from 'recharts'

const SECTOR_COLORS = [
  '#0050B3', '#1890FF', '#40A9FF', '#69C0FF', '#52C41A',
  '#FA8C16', '#F5222D', '#8E94A9', '#722ED1', '#13C2C2',
  '#EB2F96', '#A0D911', '#FAAD14', '#2F54EB', '#597EF7',
]

const RANGO_COLORS = {
  '< SMMLV': '#F5222D',
  '1-2 SMMLV': '#FA8C16',
  '2-3 SMMLV': '#FAAD14',
  '3-5 SMMLV': '#52C41A',
  '> 5 SMMLV': '#0050B3',
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

export default function EmpleoTab() {
  const { empleoData, fetchEmpleo, errors } = useStore()

  useEffect(() => { fetchEmpleo() }, [])

  if (errors.empleo) return <ErrorBanner message={errors.empleo} />
  if (!empleoData) return <SkeletonTab />

  const { stats, serie, skills, salarios, sectores } = empleoData

  return (
    <div className="fade-in">
      <h3 className="section-title">Mercado Laboral de Uraba</h3>

      {/* KPI Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 16 }}>
        <div style={{ background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border)', padding: '10px 12px' }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-primary)' }}>
            {fmt(stats.total_ofertas)}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Ofertas totales</div>
        </div>
        <div style={{ background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border)', padding: '10px 12px' }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
            {stats.salario_promedio ? fmtSalary(stats.salario_promedio) : '---'}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Salario promedio</div>
        </div>
        <div style={{ background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border)', padding: '10px 12px' }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
            {fmt(stats.por_fuente?.length)}
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Fuentes activas</div>
        </div>
      </div>

      {/* Ofertas por Municipio */}
      {stats.por_municipio?.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11 }}>Ofertas por Municipio</h4>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={stats.por_municipio} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <YAxis dataKey="municipio" type="category" tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} width={80} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
                formatter={(v) => [v, 'Ofertas']}
              />
              <Bar dataKey="total" radius={[0, 4, 4, 0]}>
                {stats.por_municipio.map((_, i) => (
                  <Cell key={i} fill={SECTOR_COLORS[i % SECTOR_COLORS.length]} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="data-source">Fuente: Scraping multi-portal</div>
            <ExportCSVButton rows={stats.por_municipio} filename="empleo_por_municipio.csv" />
          </div>
        </>
      )}

      {/* Distribución por Sector */}
      {sectores?.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Sectores Economicos</h4>
          <ResponsiveContainer width="100%" height={Math.max(160, sectores.length * 22)}>
            <BarChart data={sectores.slice(0, 10)} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <YAxis
                dataKey="sector"
                type="category"
                tick={{ fill: 'var(--text-secondary)', fontSize: 8 }}
                width={120}
                tickFormatter={(v) => v.length > 18 ? v.slice(0, 18) + '...' : v}
              />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
                formatter={(v, name) => [v, name === 'ofertas' ? 'Ofertas' : name]}
                labelFormatter={(l, payload) => payload?.[0]?.payload?.sector || l}
              />
              <Bar dataKey="ofertas" radius={[0, 4, 4, 0]}>
                {sectores.slice(0, 10).map((_, i) => (
                  <Cell key={i} fill={SECTOR_COLORS[i % SECTOR_COLORS.length]} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="data-source">{sectores.length} sectores identificados</div>
            <ExportCSVButton rows={sectores} filename="empleo_sectores.csv" />
          </div>
        </>
      )}

      {/* Serie Temporal */}
      {serie?.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Ofertas por Mes</h4>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={serie}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis dataKey="periodo" tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} angle={-45} textAnchor="end" height={40} />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
                labelStyle={{ color: 'var(--text-primary)', fontWeight: 600 }}
              />
              <Area type="monotone" dataKey="ofertas" stroke="#0050B3" fill="#0050B3" fillOpacity={0.15} strokeWidth={2} name="Ofertas" />
              <Area type="monotone" dataKey="empresas" stroke="#52C41A" fill="#52C41A" fillOpacity={0.1} strokeWidth={1.5} name="Empresas" />
            </AreaChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="data-source">Serie temporal de ofertas</div>
            <ExportCSVButton rows={serie} filename="empleo_serie_temporal.csv" />
          </div>
        </>
      )}

      {/* Top Habilidades */}
      {skills?.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Habilidades mas Demandadas</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
            {skills.slice(0, 15).map((s, i) => (
              <span
                key={s.skill}
                style={{
                  padding: '4px 10px',
                  borderRadius: 12,
                  fontSize: 11,
                  fontWeight: 500,
                  background: i < 3 ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                  color: i < 3 ? '#fff' : 'var(--text-primary)',
                  border: i >= 3 ? '1px solid var(--border)' : 'none',
                }}
              >
                {s.skill} ({s.demanda})
              </span>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="data-source">Extraido de {stats.total_ofertas} ofertas via NLP</div>
            <ExportCSVButton rows={skills} filename="empleo_skills.csv" />
          </div>
        </>
      )}

      {/* Distribución Salarial */}
      {salarios?.rangos?.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Distribucion Salarial</h4>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie
                data={salarios.rangos}
                dataKey="ofertas"
                nameKey="rango"
                cx="50%"
                cy="50%"
                outerRadius={70}
                label={({ rango, ofertas }) => `${rango}: ${ofertas}`}
                labelLine={{ stroke: 'var(--text-muted)', strokeWidth: 1 }}
              >
                {salarios.rangos.map((entry, i) => (
                  <Cell
                    key={entry.rango}
                    fill={RANGO_COLORS[entry.rango] || SECTOR_COLORS[i % SECTOR_COLORS.length]}
                    fillOpacity={0.85}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="data-source">
              {stats.con_salario} ofertas con salario ({stats.total_ofertas > 0 ? Math.round(stats.con_salario / stats.total_ofertas * 100) : 0}%)
            </div>
            <ExportCSVButton rows={salarios.rangos} filename="empleo_salarios.csv" />
          </div>
        </>
      )}

      {/* Top Empresas */}
      {stats.top_empresas?.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Top Empleadores</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {stats.top_empresas.slice(0, 10).map((e, i) => (
              <div key={i} style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '5px 10px', background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)',
              }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>
                  <span style={{ color: 'var(--text-muted)', marginRight: 6, fontWeight: 700 }}>#{i + 1}</span>
                  {e.empresa}
                </span>
                <span style={{ color: 'var(--accent-primary)', fontSize: 12, fontWeight: 600 }}>
                  {e.total}
                </span>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 }}>
            <div className="data-source">Empresas con mas vacantes publicadas</div>
            <ExportCSVButton rows={stats.top_empresas} filename="empleo_empresas.csv" />
          </div>
        </>
      )}

      {/* Fuentes */}
      {stats.por_fuente?.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Fuentes de Datos</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {stats.por_fuente.map((f, i) => (
              <div key={f.fuente} style={{
                padding: '6px 12px', borderRadius: 8,
                background: 'var(--bg-card)', border: '1px solid var(--border)',
                fontSize: 11, textAlign: 'center',
              }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
                  {f.fuente}
                </div>
                <div style={{ color: 'var(--accent-primary)', fontWeight: 700, fontSize: 14 }}>{f.total}</div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

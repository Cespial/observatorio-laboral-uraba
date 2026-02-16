import { useEffect } from 'react'
import { useStore } from '../store'
import { SkeletonTab, ErrorBanner, ExportCSVButton } from './Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, AreaChart, Area, Cell, PieChart, Pie,
} from 'recharts'

const SECTOR_COLORS = ['#0050B3', '#1890FF', '#40A9FF', '#69C0FF', '#52C41A', '#FA8C16', '#F5222D', '#8E94A9']

export default function EconomiaTab() {
  const { economiaData, fetchEconomia, errors } = useStore()

  useEffect(() => { fetchEconomia() }, [])

  if (errors.economia) return <ErrorBanner message={errors.economia} />
  if (!economiaData) return <SkeletonTab />

  const { internet, secop, turismo, terridata_economia } = economiaData

  // GDP sectors from TerriData (filter percentage-based indicators that represent sector share)
  const sectorIndicators = [
    'Agricultura, ganadería, caza, silvicultura y pesca',
    'Comercio, reparación, restaurantes y hoteles',
    'Construcción',
    'Actividades de servicios sociales y personales',
    'Establecimientos financieros, seguros y otros servicios',
    'Industria manufacturera',
    'Transporte, almacenamiento y comunicaciones',
    'Suministro de electricidad, gas y agua',
  ]

  const sectorData = sectorIndicators
    .map((name) => {
      const row = terridata_economia?.find((r) => r.indicador === name)
      return row ? { sector: name.length > 22 ? name.slice(0, 22) + '...' : name, full: name, pct: row.dato_numerico, anio: row.anio } : null
    })
    .filter(Boolean)
    .sort((a, b) => b.pct - a.pct)

  // SECOP top 5 contract types
  const secopTop = secop
    ?.filter((r) => r.tipo_de_contrato)
    .slice(0, 6)
    .map((r) => ({
      tipo: r.tipo_de_contrato?.length > 20 ? r.tipo_de_contrato.slice(0, 20) + '...' : r.tipo_de_contrato,
      full: r.tipo_de_contrato,
      contratos: r.contratos,
      valor: Math.round((r.valor_total || 0) / 1e6),
    })) || []

  // Turismo
  const turismoTop = turismo?.detalle?.slice(0, 6).map((r) => ({
    cat: r.categoria?.length > 25 ? r.categoria.slice(0, 25) + '...' : r.categoria,
    full: r.categoria,
    n: r.establecimientos,
  })) || []

  return (
    <div className="fade-in">
      <h3 className="section-title">Economia y Competitividad</h3>

      {/* GDP Sector composition */}
      {sectorData.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11 }}>Composicion del PIB por Sector</h4>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={sectorData} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} unit="%" />
              <YAxis dataKey="sector" type="category" tick={{ fill: 'var(--text-secondary)', fontSize: 8 }} width={120} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
                formatter={(v) => [`${v.toFixed(1)}%`, 'Participacion']}
                labelFormatter={(l, payload) => payload?.[0]?.payload?.full || l}
              />
              <Bar dataKey="pct" radius={[0, 4, 4, 0]}>
                {sectorData.map((_, i) => (
                  <Cell key={i} fill={SECTOR_COLORS[i % SECTOR_COLORS.length]} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="data-source">Fuente: DNP — TerriData ({sectorData[0]?.anio})</div>
            <ExportCSVButton rows={sectorData} filename="economia_pib_sectores.csv" />
          </div>
        </>
      )}

      {/* Internet Access */}
      {internet?.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Accesos Internet Fijo</h4>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={internet}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis dataKey="anio" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
                labelStyle={{ color: 'var(--text-primary)', fontWeight: 600 }}
                formatter={(v) => [v.toLocaleString('es-CO'), 'Accesos']}
              />
              <Area type="monotone" dataKey="total_accesos" stroke="#0050B3" fill="#0050B3" fillOpacity={0.15} strokeWidth={2} name="Accesos" />
            </AreaChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="data-source">Fuente: MinTIC — datos.gov.co</div>
            <ExportCSVButton rows={internet} filename="economia_internet.csv" />
          </div>
        </>
      )}

      {/* SECOP Contracts */}
      {secopTop.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Contratacion Publica (SECOP)</h4>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={secopTop} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <YAxis dataKey="tipo" type="category" tick={{ fill: 'var(--text-secondary)', fontSize: 8 }} width={110} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
                formatter={(v, name) => [v.toLocaleString('es-CO'), name === 'contratos' ? 'Contratos' : 'Valor (M COP)']}
                labelFormatter={(l, payload) => payload?.[0]?.payload?.full || l}
              />
              <Bar dataKey="contratos" fill="#0050B3" opacity={0.85} radius={[0, 4, 4, 0]} name="contratos" />
            </BarChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="data-source">Fuente: SECOP II — datos.gov.co ({secop.reduce((s, r) => s + r.contratos, 0).toLocaleString('es-CO')} contratos)</div>
            <ExportCSVButton rows={secopTop} filename="economia_secop.csv" />
          </div>
        </>
      )}

      {/* Tourism */}
      {turismoTop.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Turismo (RNT)</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {turismoTop.map((r, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 10px', background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>{r.cat}</span>
                <span style={{ color: 'var(--accent-primary)', fontSize: 11, fontWeight: 600 }}>{r.n}</span>
              </div>
            ))}
          </div>
          <div className="data-source" style={{ marginTop: 6 }}>Fuente: MinCIT — RNT via datos.gov.co ({turismo?.total} estab.)</div>
        </>
      )}
    </div>
  )
}

import { useEffect } from 'react'
import { useStore } from '../store'
import { SkeletonTab, ErrorBanner, ExportCSVButton } from './Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, RadarChart, Radar, PolarGrid,
  PolarAngleAxis, PolarRadiusAxis, Legend,
} from 'recharts'

const KPI_STYLE = {
  background: 'var(--bg-card)',
  borderRadius: 8,
  border: '1px solid var(--border)',
  padding: '10px 14px',
  flex: '1 1 45%',
  minWidth: 140,
}

export default function GobiernoTab() {
  const { gobiernoData, fetchGobierno, errors } = useStore()

  useEffect(() => { fetchGobierno() }, [])

  if (errors.gobierno) return <ErrorBanner message={errors.gobierno} />
  if (!gobiernoData) return <SkeletonTab />

  const { finanzas, desempeno, digital, pobreza } = gobiernoData

  // Key fiscal KPIs
  const fiscalKpis = [
    { key: 'Ingresos totales', label: 'Ingresos Totales', unit: 'M COP', divisor: 1 },
    { key: 'Gastos totales', label: 'Gastos Totales', unit: 'M COP', divisor: 1 },
    { key: 'Gastos de capital (Inversión)', label: 'Inversion', unit: 'M COP', divisor: 1 },
    { key: 'Indicador de desempeño fiscal', label: 'Desempeno Fiscal', unit: 'pts', divisor: 1 },
    { key: 'Capacidad de ahorro', label: 'Cap. Ahorro', unit: '%', divisor: 1 },
    { key: 'Dependencia de las transferencias', label: 'Dep. Transferencias', unit: '%', divisor: 1 },
  ]

  const fiscalData = fiscalKpis.map((k) => {
    const row = finanzas?.find((r) => r.indicador === k.key)
    return { ...k, value: row?.dato_numerico, anio: row?.anio }
  }).filter((k) => k.value != null)

  // MDM radar chart with benchmarking - Apartadó vs Group Average
  const mdmPairs = [
    { name: 'Educacion', indicator: 'Educación', avg: 'Promedio de educación por grupo de DI' },
    { name: 'Salud', indicator: 'Salud', avg: 'Promedio de salud por grupo de DI' },
    { name: 'Seguridad', indicator: 'Seguridad', avg: 'Promedio de seguridad por grupo de DI' },
    { name: 'Serv. Publicos', indicator: 'Acceso a servicios públicos', avg: 'Promedio de servicios públicos por grupo de DI' },
    { name: 'Transparencia', indicator: 'Gobierno abierto y transparencia', avg: 'Promedio de gobierno abierto y transparencia por grupo de DI' },
    { name: 'Movilizacion', indicator: 'Movilización de recursos', avg: 'Promedio de movilización de recursos por grupo de DI' },
  ]

  const radarData = mdmPairs.map((p) => {
    const row = desempeno?.find((r) => r.indicador === p.indicator)
    const avgRow = desempeno?.find((r) => r.indicador === p.avg)
    return {
      subject: p.name,
      apartado: row?.dato_numerico || 0,
      promedio: avgRow?.dato_numerico || 0,
    }
  })

  // MDM summary
  const mdmTotal = desempeno?.find((r) => r.indicador === 'MDM')
  const mdmPos = desempeno?.find((r) => r.indicador === 'MDM - Posición')
  const mdmAvg = desempeno?.find((r) => r.indicador === 'Promedio MDM por grupo de DI')

  // Gobierno Digital comparison - main index per year
  const digitalByYear = {}
  digital?.filter((r) => r.indice === 'Gobierno Digital').forEach((r) => {
    if (!digitalByYear[r.anio]) {
      digitalByYear[r.anio] = { anio: r.anio, apartado: 0, promedio: 0, max: 0, min: 0 }
    }
    digitalByYear[r.anio].apartado = Math.round(r.puntaje * 10) / 10
    digitalByYear[r.anio].promedio = Math.round(r.promedio_grupo * 10) / 10
    digitalByYear[r.anio].max = Math.round((r.m_ximo_grupo ?? 0) * 10) / 10
    digitalByYear[r.anio].min = Math.round((r.m_nimo_grupo ?? 0) * 10) / 10
  })
  const digitalMain = Object.values(digitalByYear).sort((a, b) => a.anio - b.anio)

  // Poverty
  const ipm = pobreza?.terridata?.find((r) => r.indicador === 'Índice de pobreza multidimensional - IPM')
  const ipmCab = pobreza?.terridata?.find((r) => r.indicador === 'IPM - Cabecera')
  const ipmRur = pobreza?.terridata?.find((r) => r.indicador === 'IPM - Rural')
  // National IPM 2018 reference
  const ipmNacional = 19.6

  return (
    <div className="fade-in">
      <h3 className="section-title">Gobierno y Finanzas Publicas</h3>

      {/* MDM Summary with benchmark */}
      {mdmTotal && (
        <div style={{ background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border)', padding: '10px 14px', marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Desempeno Municipal (MDM)</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--accent-primary)' }}>{mdmTotal.dato_numerico?.toFixed(1)}</div>
              {mdmAvg && (
                <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                  Prom. grupo: <strong style={{ color: 'var(--text-secondary)' }}>{mdmAvg.dato_numerico?.toFixed(1)}</strong>
                  {mdmTotal.dato_numerico > mdmAvg.dato_numerico
                    ? <span style={{ color: 'var(--semantic-positive)', marginLeft: 6 }}>&#9650; sobre promedio</span>
                    : <span style={{ color: 'var(--semantic-negative)', marginLeft: 6 }}>&#9660; bajo promedio</span>
                  }
                </div>
              )}
            </div>
            {mdmPos && (
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Posicion Nacional</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>#{mdmPos.dato_numerico?.toFixed(0)}</div>
                <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>de 1,122 municipios</div>
              </div>
            )}
          </div>
          <div style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 4 }}>Fuente: DNP — TerriData ({mdmTotal.anio})</div>
        </div>
      )}

      {/* MDM Radar with benchmark overlay */}
      {radarData.some((r) => r.apartado > 0) && (
        <>
          <h4 className="section-title" style={{ fontSize: 11 }}>Componentes MDM — Apartado vs Promedio Grupo</h4>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData} outerRadius={75}>
              <PolarGrid stroke="var(--border)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-secondary)', fontSize: 8 }} />
              <PolarRadiusAxis tick={{ fill: 'var(--text-muted)', fontSize: 8 }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
                formatter={(v, name) => [v.toFixed(1), name === 'apartado' ? 'Apartado' : 'Prom. Grupo']}
              />
              <Legend wrapperStyle={{ fontSize: 10 }} />
              <Radar dataKey="promedio" stroke="#DDE1E8" fill="#DDE1E8" fillOpacity={0.3} strokeWidth={1.5} strokeDasharray="4 3" name="Prom. Grupo" />
              <Radar dataKey="apartado" stroke="var(--accent-primary)" fill="var(--accent-primary)" fillOpacity={0.2} strokeWidth={2} name="Apartado" />
            </RadarChart>
          </ResponsiveContainer>
          <div className="data-source">Fuente: DNP — TerriData</div>
        </>
      )}

      {/* Fiscal KPIs */}
      {fiscalData.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Finanzas Publicas</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {fiscalData.map((k) => (
              <div key={k.label} style={KPI_STYLE}>
                <div style={{ fontSize: 10, color: 'var(--text-secondary)', marginBottom: 2 }}>{k.label}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                  {typeof k.value === 'number'
                    ? (k.unit === 'M COP' ? `$${(k.value / 1).toLocaleString('es-CO', { maximumFractionDigits: 0 })}` : k.value.toFixed(1))
                    : k.value}
                  <span style={{ fontSize: 9, fontWeight: 400, color: 'var(--text-muted)', marginLeft: 2 }}>{k.unit}</span>
                </div>
                {k.anio && <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>{k.anio}</div>}
              </div>
            ))}
          </div>
          <div className="data-source" style={{ marginTop: 6 }}>Fuente: DNP — TerriData</div>
        </>
      )}

      {/* Gobierno Digital with benchmark range */}
      {digitalMain.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Gobierno Digital — Apartado vs Grupo</h4>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={digitalMain}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis dataKey="anio" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
                labelStyle={{ color: 'var(--text-primary)', fontWeight: 600 }}
              />
              <Bar dataKey="apartado" fill="var(--accent-primary)" opacity={0.85} radius={[4, 4, 0, 0]} name="Apartado" />
              <Bar dataKey="promedio" fill="var(--border)" opacity={0.6} radius={[4, 4, 0, 0]} name="Prom. Grupo" />
            </BarChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="data-source">Fuente: MinTIC — Gobierno Digital via datos.gov.co</div>
            <ExportCSVButton rows={digitalMain} filename="gobierno_digital.csv" />
          </div>
        </>
      )}

      {/* Poverty with national benchmark */}
      {ipm && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Pobreza Multidimensional (IPM)</h4>
          <div style={{ display: 'flex', gap: 6 }}>
            <div style={{ ...KPI_STYLE, textAlign: 'center' }}>
              <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Apartado</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--semantic-negative)' }}>{ipm.dato_numerico?.toFixed(1)}%</div>
              <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>{ipm.anio}</div>
            </div>
            {ipmCab && (
              <div style={{ ...KPI_STYLE, textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Cabecera</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--semantic-warning)' }}>{ipmCab.dato_numerico?.toFixed(1)}%</div>
              </div>
            )}
            {ipmRur && (
              <div style={{ ...KPI_STYLE, textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Rural</div>
                <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--semantic-negative)' }}>{ipmRur.dato_numerico?.toFixed(1)}%</div>
              </div>
            )}
          </div>
          <div style={{ marginTop: 8, padding: '6px 10px', background: 'var(--bg-card)', borderRadius: 6, border: '1px solid var(--border)', fontSize: 11 }}>
            <span style={{ color: 'var(--text-secondary)' }}>Referencia nacional: </span>
            <strong style={{ color: 'var(--text-primary)' }}>{ipmNacional}%</strong>
            <span style={{ marginLeft: 8, color: ipm.dato_numerico > ipmNacional ? 'var(--semantic-negative)' : 'var(--semantic-positive)' }}>
              {ipm.dato_numerico > ipmNacional
                ? `${(ipm.dato_numerico - ipmNacional).toFixed(1)}pp sobre nacional`
                : `${(ipmNacional - ipm.dato_numerico).toFixed(1)}pp bajo nacional`
              }
            </span>
          </div>
          <div className="data-source" style={{ marginTop: 6 }}>Fuente: DNP — TerriData (IPM Nacional 2018: DANE)</div>
        </>
      )}
    </div>
  )
}

import { useState, useEffect } from 'react'
import { useStore } from '../store'
import { SkeletonTab, ErrorBanner, ExportCSVButton } from './Skeleton'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, LineChart, Line, Cell,
} from 'recharts'

const KPI_STYLE = {
  background: 'var(--bg-card)',
  borderRadius: 8,
  border: '1px solid var(--border)',
  padding: '10px 14px',
  flex: '1 1 45%',
  minWidth: 140,
}

export default function SaludTab() {
  const { saludData, fetchSalud, errors } = useStore()

  useEffect(() => { fetchSalud() }, [])

  if (errors.salud) return <ErrorBanner message={errors.salud} />
  if (!saludData) return <SkeletonTab />

  const { terridata, irca, sivigila } = saludData

  // Key TerriData KPIs
  const kpis = [
    { key: 'Afiliados al SGSSS', label: 'Afiliados SGSSS', color: '#0050B3' },
    { key: 'Cobertura del régimen subsidiado', label: 'Cob. Subsidiado', color: '#52C41A', suffix: '%' },
    { key: 'Cobertura vacunación pentavalente en menores de 1 año', label: 'Vacunacion <1a', color: '#FA8C16', suffix: '%' },
    { key: 'Tasa de mortalidad infantil en menores de 1 año (x cada 1.000 nacidos vivos)', label: 'Mort. Infantil', color: '#F5222D', suffix: '/1000 NV' },
    { key: 'Tasa de mortalidad (x cada 1.000 habitantes)', label: 'Mort. General', color: '#F5222D', suffix: '/1000 hab' },
    { key: 'Razón de mortalidad materna a 42 días', label: 'Mort. Materna', color: '#F5222D', suffix: '/100k NV' },
  ]

  const kpiData = kpis.map((k) => {
    const row = terridata?.find((r) => r.indicador === k.key)
    return { ...k, value: row?.dato_numerico, anio: row?.anio }
  }).filter((k) => k.value != null)

  // IRCA chart
  const ircaChart = irca
    ?.filter((r) => r.irca_total != null)
    .map((r) => ({
      anio: r.anio,
      urbano: r.irca_urbano,
      rural: r.irca_rural,
      total: r.irca_total,
    })) || []

  // Top Sivigila events
  const sivigilaTop = sivigila?.slice(0, 8).map((r) => ({
    evento: r.evento?.length > 28 ? r.evento.slice(0, 28) + '...' : r.evento,
    full: r.evento,
    casos: r.total_casos,
  })) || []

  const SIVIGILA_COLORS = ['#0050B3', '#1890FF', '#40A9FF', '#69C0FF', '#91D5FF', '#B7DCFF', '#D6EBFF', '#E6F4FF']

  return (
    <div className="fade-in">
      <h3 className="section-title">Salud Publica</h3>

      {/* KPI cards */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
        {kpiData.map((k) => (
          <div key={k.label} style={KPI_STYLE}>
            <div style={{ fontSize: 10, color: 'var(--text-secondary)', marginBottom: 2 }}>{k.label}</div>
            <div style={{ fontSize: 18, fontWeight: 700, color: k.color }}>
              {typeof k.value === 'number' ? k.value.toLocaleString('es-CO') : k.value}
              {k.suffix && <span style={{ fontSize: 10, fontWeight: 400, color: 'var(--text-muted)', marginLeft: 2 }}>{k.suffix}</span>}
            </div>
            {k.anio && <div style={{ fontSize: 9, color: 'var(--text-muted)' }}>{k.anio}</div>}
          </div>
        ))}
      </div>

      {/* IRCA Water Quality */}
      {ircaChart.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11 }}>Calidad del Agua (IRCA)</h4>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={ircaChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis dataKey="anio" tick={{ fill: 'var(--text-secondary)', fontSize: 9 }} />
              <YAxis tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} domain={[0, 'auto']} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
                labelStyle={{ color: 'var(--text-primary)', fontWeight: 600 }}
              />
              <Line type="monotone" dataKey="urbano" stroke="#0050B3" strokeWidth={2} dot={{ r: 3 }} name="Urbano" />
              <Line type="monotone" dataKey="rural" stroke="#FA8C16" strokeWidth={2} dot={{ r: 3 }} name="Rural" connectNulls />
              <Line type="monotone" dataKey="total" stroke="#52C41A" strokeWidth={2} dot={{ r: 3 }} name="Total" />
            </LineChart>
          </ResponsiveContainer>
          <div style={{ fontSize: 9, color: 'var(--text-muted)', marginBottom: 4, fontStyle: 'italic' }}>
            0-5: Sin riesgo | 5.1-14: Bajo | 14.1-35: Medio | 35.1-80: Alto | {'>'}80: Inviable
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="data-source">Fuente: INS — IRCA via datos.gov.co</div>
            <ExportCSVButton rows={ircaChart} filename="irca_calidad_agua.csv" />
          </div>
        </>
      )}

      {/* Sivigila Epidemiological Events */}
      {sivigilaTop.length > 0 && (
        <>
          <h4 className="section-title" style={{ fontSize: 11, marginTop: 16 }}>Eventos Epidemiologicos (SIVIGILA)</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={sivigilaTop} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-light)" />
              <XAxis type="number" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
              <YAxis dataKey="evento" type="category" tick={{ fill: 'var(--text-secondary)', fontSize: 8 }} width={130} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
                formatter={(v) => [v.toLocaleString('es-CO'), 'Casos']}
                labelFormatter={(l, payload) => payload?.[0]?.payload?.full || l}
              />
              <Bar dataKey="casos" radius={[0, 4, 4, 0]}>
                {sivigilaTop.map((_, i) => (
                  <Cell key={i} fill={SIVIGILA_COLORS[i % SIVIGILA_COLORS.length]} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div className="data-source">Fuente: INS — SIVIGILA via datos.gov.co</div>
            <ExportCSVButton rows={sivigilaTop} filename="sivigila_eventos.csv" />
          </div>
        </>
      )}
    </div>
  )
}

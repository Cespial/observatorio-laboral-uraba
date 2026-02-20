import { useEffect } from 'react'
import { useStore } from '../store'

const CARDS = [
  { key: 'empleo_ofertas', label: 'Ofertas laborales', source: 'Multi-portal', accent: true },
  { key: 'empleo_empresas', label: 'Empresas contratando', source: 'Multi-portal', accent: true },
  { key: 'empleo_salario', label: 'Salario promedio', source: 'Multi-portal', format: 'salary' },
  { key: 'poblacion_total', label: 'Poblacion total', source: 'DANE', yearKey: 'poblacion_anio' },
  { key: 'establecimientos_comerciales', label: 'Negocios mapeados', source: 'Google Places' },
  { key: 'establecimientos_educativos', label: 'Establec. educativos', source: 'MEN' },
  { key: 'ips_salud', label: 'IPS habilitadas', source: 'REPS' },
  { key: 'total_homicidios', label: 'Homicidios', source: 'Policia Nal.', negative: true },
  { key: 'total_hurtos', label: 'Hurtos', source: 'Policia Nal.', negative: true },
  { key: 'total_victimas_conflicto', label: 'Victimas conflicto', source: 'Unidad Victimas', negative: true },
]

function fmt(val) {
  if (val == null) return '---'
  if (typeof val === 'number') return val.toLocaleString('es-CO')
  return String(val)
}

function fmtSalary(val) {
  if (val == null) return '---'
  return `$${(val / 1000000).toFixed(1)}M`
}

export default function KPICards({ summary }) {
  const errors = useStore(s => s.errors)
  const empleoKpis = useStore(s => s.empleoKpis)
  const fetchEmpleoKpis = useStore(s => s.fetchEmpleoKpis)

  useEffect(() => { fetchEmpleoKpis() }, [])

  if (errors.summary) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '10px 24px', fontSize: 13, color: 'var(--semantic-negative)' }}>
        Error al cargar indicadores: {errors.summary}
      </div>
    )
  }

  if (!summary || summary.municipio === 'Error') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '10px 24px', fontSize: 13, color: 'var(--text-muted)' }}>
        Cargando indicadores territoriales...
      </div>
    )
  }

  return (
    <div className="kpi-strip" style={{ display: 'flex', gap: 12, padding: '10px 24px', overflowX: 'auto', flexShrink: 0, background: 'var(--bg-primary)', borderBottom: '1px solid var(--border)' }}>
      {CARDS.map((card) => {
        let val
        if (card.key === 'empleo_ofertas') val = empleoKpis?.total_ofertas
        else if (card.key === 'empleo_empresas') val = empleoKpis?.total_empresas
        else if (card.key === 'empleo_salario') val = empleoKpis?.salario_promedio
        else if (card.key === 'icfes_promedio') val = summary.icfes?.promedio_global
        else val = summary[card.key]
        const year = card.yearKey ? summary[card.yearKey] : null
        return (
          <div
            key={card.key}
            className="card"
            style={{ padding: '10px 14px', minWidth: 130, flexShrink: 0 }}
          >
            <div
              style={{
                fontSize: 20,
                fontWeight: 700,
                color: card.negative ? 'var(--semantic-negative)' : card.accent ? 'var(--accent-primary)' : 'var(--text-primary)',
                lineHeight: 1.2,
                fontFeatureSettings: '"tnum"',
              }}
            >
              {card.format === 'salary' ? fmtSalary(val) : fmt(val)}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>
              {card.label}
            </div>
            <div className="font-mono" style={{ fontSize: 9, color: 'var(--text-muted)', marginTop: 3 }}>
              {card.source}{year ? ` \u00B7 ${year}` : ''}
            </div>
          </div>
        )
      })}
    </div>
  )
}

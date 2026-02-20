const CARDS = [
  { key: 'poblacion_total', label: 'Poblacion total', source: 'DANE', yearKey: 'poblacion_anio' },
  { key: 'manzanas_censales', label: 'Manzanas censales', source: 'MGN-DANE' },
  { key: 'establecimientos_comerciales', label: 'Negocios mapeados', source: 'Google Places' },
  { key: 'establecimientos_educativos', label: 'Establec. educativos', source: 'MEN' },
  { key: 'matricula_total', label: 'Matricula total', source: 'MEN' },
  { key: 'ips_salud', label: 'IPS habilitadas', source: 'REPS' },
  { key: 'prestadores_servicios', label: 'Prestadores serv.', source: 'SuperServ.' },
  { key: 'total_homicidios', label: 'Homicidios', source: 'Policia Nal.', negative: true },
  { key: 'total_hurtos', label: 'Hurtos', source: 'Policia Nal.', negative: true },
  { key: 'total_vif', label: 'Violencia intraf.', source: 'Policia Nal.', negative: true },
  { key: 'total_victimas_conflicto', label: 'Victimas conflicto', source: 'Unidad Victimas', negative: true },
]

function fmt(val) {
  if (val == null) return '---'
  if (typeof val === 'number') return val.toLocaleString('es-CO')
  return String(val)
}

export default function KPICards({ summary }) {
  const errors = useStore(s => s.errors)

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
        const val = card.key === 'icfes_promedio' ? summary.icfes?.promedio_global : summary[card.key]
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
                color: card.negative ? 'var(--semantic-negative)' : 'var(--text-primary)',
                lineHeight: 1.2,
                fontFeatureSettings: '"tnum"',
              }}
            >
              {fmt(val)}
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

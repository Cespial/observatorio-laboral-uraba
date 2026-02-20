import { useState, useEffect } from 'react'
import { useStore } from '../store'

const DISMISSED_KEY = 'observatorio-welcome-dismissed-v2'

export default function WelcomeOverlay() {
  const [visible, setVisible] = useState(false)
  const [closing, setClosing] = useState(false)
  const catalogSummary = useStore((s) => s.catalogSummary)

  useEffect(() => {
    if (!localStorage.getItem(DISMISSED_KEY)) {
      setVisible(true)
    }
  }, [])

  const dismiss = () => {
    setClosing(true)
    setTimeout(() => {
      setVisible(false)
      localStorage.setItem(DISMISSED_KEY, '1')
    }, 300)
  }

  if (!visible) return null

  return (
    <div
      onClick={dismiss}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'rgba(0,0,0,0.55)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        opacity: closing ? 0 : 1,
        transition: 'opacity 0.3s ease',
        cursor: 'pointer',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--bg-primary)',
          borderRadius: 16,
          padding: '36px 40px',
          maxWidth: 520,
          width: '90%',
          boxShadow: '0 12px 40px rgba(0,0,0,0.25)',
          transform: closing ? 'scale(0.95)' : 'scale(1)',
          transition: 'transform 0.3s ease',
        }}
      >
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent-primary)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 8 }}>
          Observatorio Laboral
        </div>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2, marginBottom: 8 }}>
          Region de Uraba, Antioquia
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 20 }}>
          Plataforma de inteligencia territorial con enfoque en el
          {' '}<strong>mercado laboral</strong> de los 11 municipios de Uraba.
          Integra datos de <strong>empleo</strong>, <strong>economia</strong>,
          {' '}<strong>educacion</strong>, <strong>salud</strong> y <strong>seguridad</strong> para
          facilitar la toma de decisiones basada en evidencia.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 24 }}>
          {[
            { n: '368+', label: 'Ofertas laborales' },
            { n: '6', label: 'Fuentes de empleo' },
            { n: '11', label: 'Municipios cubiertos' },
            { n: catalogSummary ? String(catalogSummary.tables) : '...', label: 'Tablas de datos' },
          ].map((s) => (
            <div key={s.label} style={{ padding: '10px 14px', background: 'var(--bg-secondary)', borderRadius: 8, border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-primary)' }}>{s.n}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{s.label}</div>
            </div>
          ))}
        </div>

        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 20, lineHeight: 1.5 }}>
          Fuentes: Computrabajo, ElEmpleo, Indeed, LinkedIn, Comfama, Comfenalco, DANE, DNP-TerriData, Policia Nacional, ICFES, MinSalud, MinTIC, Google Places
        </div>

        <button
          onClick={dismiss}
          style={{
            width: '100%',
            padding: '12px 0',
            background: 'var(--accent-primary)',
            color: '#FFFFFF',
            border: 'none',
            borderRadius: 8,
            fontSize: 14,
            fontWeight: 600,
            cursor: 'pointer',
            fontFamily: 'inherit',
          }}
        >
          Explorar el observatorio
        </button>
      </div>
    </div>
  )
}

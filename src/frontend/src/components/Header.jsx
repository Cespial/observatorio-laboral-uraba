import { useStore } from '../store'

export default function Header() {
  const theme = useStore((s) => s.theme)
  const toggleTheme = useStore((s) => s.toggleTheme)
  const showToast = useStore((s) => s.showToast)
  const catalogSummary = useStore((s) => s.catalogSummary)
  const selectedMunicipio = useStore((s) => s.selectedMunicipio)
  const municipios = useStore((s) => s.municipios)
  const setSelectedMunicipio = useStore((s) => s.setSelectedMunicipio)
  const activeView = useStore((s) => s.activeView)
  const setActiveView = useStore((s) => s.setActiveView)

  return (
    <header
      style={{
        height: 56,
        background: 'var(--bg-primary)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        flexShrink: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '0.02em' }}>
            Observatorio Laboral
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            Uraba, Antioquia
          </div>
        </div>
        <div style={{ width: 1, height: 32, background: 'var(--border)', margin: '0 8px' }} />
        
        {/* Territorial Context Selector */}
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 11, color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 600 }}>Vista:</span>
          <div style={{ position: 'relative' }}>
            <select
              value={selectedMunicipio}
              onChange={(e) => setSelectedMunicipio(e.target.value)}
              style={{
                background: 'var(--bg-secondary)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '6px 32px 6px 12px',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer',
                outline: 'none',
                appearance: 'none',
                boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                transition: 'all 0.2s ease'
              }}
              onFocus={(e) => e.target.style.borderColor = 'var(--accent-primary)'}
              onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
            >
              {municipios.map(m => (
                <option key={m.name} value={m.name}>{m.name}</option>
              ))}
            </select>
            <span style={{
              position: 'absolute',
              right: '10px',
              top: '50%',
              transform: 'translateY(-50%)',
              pointerEvents: 'none',
              fontSize: '10px',
              color: 'var(--text-muted)'
            }}>▼</span>
          </div>
        </div>

        {/* View Toggle: Mapa / Tablero */}
        <div style={{
          display: 'flex', background: 'var(--bg-tertiary)',
          borderRadius: 8, border: '1px solid var(--border)',
          overflow: 'hidden',
        }}>
          {['mapa', 'tablero'].map((v) => (
            <button
              key={v}
              onClick={() => setActiveView(v)}
              style={{
                padding: '5px 14px',
                fontSize: 12,
                fontWeight: activeView === v ? 700 : 400,
                fontFamily: 'inherit',
                color: activeView === v ? '#fff' : 'var(--text-secondary)',
                background: activeView === v ? 'var(--accent-primary)' : 'transparent',
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                textTransform: 'capitalize',
              }}
            >
              {v === 'mapa' ? 'Mapa' : 'Tablero'}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <div className="header-desktop-info" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span
            style={{
              width: 7, height: 7, borderRadius: '50%',
              background: 'var(--semantic-positive)',
              display: 'inline-block',
            }}
          />
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            {catalogSummary
              ? `${catalogSummary.tables} tablas \u00B7 ${catalogSummary.records?.toLocaleString('es-CO')} registros`
              : 'Cargando...'}
          </span>
        </div>

        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          aria-label={theme === 'light' ? 'Cambiar a modo oscuro' : 'Cambiar a modo claro'}
          title={theme === 'light' ? 'Modo oscuro' : 'Modo claro'}
          style={{
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border)',
            borderRadius: 6,
            width: 32,
            height: 32,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            fontSize: 16,
            color: 'var(--text-secondary)',
          }}
        >
          {theme === 'light' ? '\u263E' : '\u2600'}
        </button>

        {/* Share / Embed */}
        <button
          onClick={() => {
            const url = `${window.location.origin}${window.location.pathname}?embed=true`
            navigator.clipboard.writeText(url)
            showToast('URL de embed copiada al portapapeles')
          }}
          aria-label="Copiar URL de embed"
          title="Copiar URL embed"
          style={{
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border)',
            borderRadius: 6,
            width: 32,
            height: 32,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            fontSize: 14,
            color: 'var(--text-secondary)',
          }}
        >
          &lt;/&gt;
        </button>
      </div>
    </header>
  )
}

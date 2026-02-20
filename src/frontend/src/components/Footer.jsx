export default function Footer() {
  return (
    <footer
      style={{
        height: 32,
        background: 'var(--bg-primary)',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        flexShrink: 0,
        fontSize: 11,
        color: 'var(--text-muted)',
      }}
    >
      <div>
        Fuentes: ComputTrabajo, elempleo, Indeed, Comfama, LinkedIn, DANE, DNP-TerriData, ICFES, Google Places
      </div>
      <div>
        Observatorio Laboral de Uraba &copy; 2026 &middot; Datos actualizados diariamente
      </div>
    </footer>
  )
}

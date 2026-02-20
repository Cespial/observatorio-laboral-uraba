export default function DashboardCard({ title, subtitle, actions, span = 1, children }) {
  return (
    <div
      className="dashboard-card card"
      style={{ gridColumn: `span ${span}` }}
    >
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
        marginBottom: 12, gap: 8,
      }}>
        <div>
          {title && (
            <h4 style={{
              fontSize: 13, fontWeight: 700, color: 'var(--text-primary)',
              textTransform: 'uppercase', letterSpacing: '0.04em', margin: 0,
            }}>
              {title}
            </h4>
          )}
          {subtitle && (
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
              {subtitle}
            </div>
          )}
        </div>
        {actions && <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>{actions}</div>}
      </div>
      {children}
    </div>
  )
}

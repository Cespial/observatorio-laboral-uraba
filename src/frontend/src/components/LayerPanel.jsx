import { useStore } from '../store';

const LAYERS = [
  { id: 'limite_municipal', label: 'Limite Municipal', color: '#0050B3' },
  { id: 'manzanas_censales', label: 'Manzanas 3D', color: '#1890FF' },
  { id: 'osm_edificaciones', label: 'Edificaciones', color: '#5E6687' },
  { id: 'osm_vias', label: 'Red Vial', color: '#40A9FF' },
  { id: 'google_places', label: 'Negocios', color: '#FA8C16' },
  { id: 'places_heatmap', label: 'Heatmap Negocios', color: '#0050B3' },
  { id: 'empleo_concentracion', label: 'Empleo Regional', color: '#FA8C16' },
];

export default function LayerPanel() {
  const activeLayers = useStore((s) => s.activeLayers);
  const toggleLayer = useStore((s) => s.toggleLayer);
  const placesCategories = useStore((s) => s.placesCategories);
  const selectedCategory = useStore((s) => s.selectedCategory);
  const setSelectedCategory = useStore((s) => s.setSelectedCategory);

  const placesActive = activeLayers.includes('google_places');

  return (
    <div
      style={{
        position: 'absolute',
        top: 12,
        left: 12,
        zIndex: 10,
        background: 'var(--bg-card)',
        borderRadius: 8,
        border: '1px solid var(--border)',
        padding: 12,
        minWidth: 190,
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      }}
    >
      <div
        style={{
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: '0.12em',
          color: 'var(--text-primary)',
          marginBottom: 8,
          textTransform: 'uppercase',
        }}
      >
        Capas
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {LAYERS.map((layer) => {
          const active = activeLayers.includes(layer.id);
          return (
            <div key={layer.id}>
              <div
                role="switch"
                aria-checked={active}
                aria-label={`Capa ${layer.label}`}
                tabIndex={0}
                onClick={() => toggleLayer(layer.id)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleLayer(layer.id); } }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  cursor: 'pointer',
                  opacity: active ? 1 : 0.45,
                  transition: 'opacity 0.2s ease',
                }}
              >
                <span
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: layer.color,
                    flexShrink: 0,
                    boxShadow: active ? `0 0 6px ${layer.color}` : 'none',
                  }}
                />
                <span style={{ fontSize: 12, color: active ? 'var(--text-primary)' : 'var(--text-secondary)', flex: 1 }}>
                  {layer.label}
                </span>
                <span
                  style={{
                    width: 28,
                    height: 14,
                    borderRadius: 7,
                    background: active ? 'rgba(0,80,179,0.2)' : 'var(--border)',
                    position: 'relative',
                    transition: 'background 0.2s ease',
                    flexShrink: 0,
                  }}
                >
                  <span
                    style={{
                      position: 'absolute',
                      top: 2,
                      left: active ? 14 : 2,
                      width: 10,
                      height: 10,
                      borderRadius: '50%',
                      background: active ? 'var(--accent-primary)' : 'var(--border)',
                      transition: 'left 0.2s ease, background 0.2s ease',
                    }}
                  />
                </span>
              </div>

              {/* Category filter for places */}
              {layer.id === 'google_places' && placesActive && placesCategories?.length > 0 && (
                <select
                  value={selectedCategory || ''}
                  onChange={(e) => setSelectedCategory(e.target.value || null)}
                  onClick={(e) => e.stopPropagation()}
                  style={{
                    marginTop: 4,
                    marginLeft: 16,
                    width: 'calc(100% - 16px)',
                    fontSize: 10,
                    padding: '3px 6px',
                    background: 'var(--bg-tertiary)',
                    color: 'var(--text-primary)',
                    border: '1px solid var(--border)',
                    borderRadius: 4,
                    outline: 'none',
                    fontFamily: 'inherit',
                  }}
                >
                  <option value="">Todas ({placesCategories.reduce((s, c) => s + c.count, 0)})</option>
                  {placesCategories.map((c) => (
                    <option key={c.category} value={c.category}>
                      {c.category} ({c.count})
                    </option>
                  ))}
                </select>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

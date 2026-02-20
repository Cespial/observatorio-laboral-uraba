import { useState, useEffect, useRef } from 'react'
import { useStore } from '../../store'
import DashboardCard from './DashboardCard'
import { ExportCSVButton } from '../Skeleton'

function StarRating({ rating }) {
  if (rating == null) return <span style={{ color: 'var(--text-muted)', fontSize: 11 }}>---</span>
  const full = Math.floor(rating)
  const half = rating - full >= 0.5
  return (
    <span style={{ color: '#FAAD14', fontSize: 13, letterSpacing: 1 }}>
      {'\u2605'.repeat(full)}{half ? '\u00BD' : ''}{'\u2606'.repeat(5 - full - (half ? 1 : 0))}
      <span style={{ color: 'var(--text-secondary)', fontSize: 11, marginLeft: 4 }}>{rating.toFixed(1)}</span>
    </span>
  )
}

export default function BusinessDirectory() {
  const {
    businessDirectory, businessDirectoryLoading, businessDirectoryParams,
    fetchBusinessDirectory, placesCategories,
  } = useStore()

  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [minRating, setMinRating] = useState(0)
  const debounceRef = useRef(null)

  // Debounced search
  useEffect(() => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      fetchBusinessDirectory({ search, category: category || null, min_rating: minRating, page: 1 })
    }, 400)
    return () => clearTimeout(debounceRef.current)
  }, [search, category, minRating])

  // Initial fetch
  useEffect(() => {
    fetchBusinessDirectory({ page: 1 })
  }, [])

  const dir = businessDirectory
  const items = dir?.items || []

  const goToPage = (page) => {
    fetchBusinessDirectory({ ...businessDirectoryParams, search, category: category || null, min_rating: minRating, page })
  }

  return (
    <DashboardCard
      span={3}
      title="Directorio de Negocios"
      subtitle={dir ? `${dir.total?.toLocaleString('es-CO')} negocios encontrados` : null}
      actions={<ExportCSVButton rows={items} filename="dashboard_directorio_negocios.csv" />}
    >
      {/* Filter Bar */}
      <div className="directory-filters">
        <input
          type="text"
          placeholder="Buscar por nombre o direccion..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            flex: 2, minWidth: 180,
            padding: '8px 12px', borderRadius: 6,
            border: '1px solid var(--border)',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            fontSize: 13, fontFamily: 'inherit',
            outline: 'none',
          }}
        />
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          style={{
            flex: 1, minWidth: 140,
            padding: '8px 12px', borderRadius: 6,
            border: '1px solid var(--border)',
            background: 'var(--bg-secondary)',
            color: 'var(--text-primary)',
            fontSize: 13, fontFamily: 'inherit',
            cursor: 'pointer', appearance: 'none',
          }}
        >
          <option value="">Todas las categorias</option>
          {placesCategories?.map(c => (
            <option key={c.category} value={c.category}>{c.category} ({c.count})</option>
          ))}
        </select>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, minWidth: 120 }}>
          <span style={{ fontSize: 11, color: 'var(--text-secondary)', whiteSpace: 'nowrap' }}>
            Rating {minRating > 0 ? `${minRating}+` : 'todos'}
          </span>
          <input
            type="range" min="0" max="5" step="0.5"
            value={minRating}
            onChange={(e) => setMinRating(Number(e.target.value))}
            style={{ width: 80 }}
          />
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto', marginTop: 12 }}>
        <table className="directory-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Categoria</th>
              <th>Rating</th>
              <th>Resenas</th>
              <th>Direccion</th>
            </tr>
          </thead>
          <tbody>
            {businessDirectoryLoading && items.length === 0 ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>Cargando...</td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan={5} style={{ textAlign: 'center', padding: 24, color: 'var(--text-muted)' }}>No se encontraron negocios</td></tr>
            ) : (
              items.map((item) => (
                <tr key={item.place_id}>
                  <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{item.name}</td>
                  <td>
                    <span className="badge badge-blue">{item.category}</span>
                  </td>
                  <td><StarRating rating={item.rating} /></td>
                  <td style={{ textAlign: 'right' }}>{item.user_ratings_total?.toLocaleString('es-CO') ?? '---'}</td>
                  <td style={{ color: 'var(--text-secondary)', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {item.address || '---'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {dir && dir.total_pages > 1 && (
        <div style={{
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          gap: 12, marginTop: 12,
        }}>
          <button
            onClick={() => goToPage(dir.page - 1)}
            disabled={dir.page <= 1}
            style={{
              padding: '6px 14px', borderRadius: 6,
              border: '1px solid var(--border)',
              background: dir.page <= 1 ? 'var(--bg-tertiary)' : 'var(--bg-secondary)',
              color: dir.page <= 1 ? 'var(--text-muted)' : 'var(--text-primary)',
              cursor: dir.page <= 1 ? 'not-allowed' : 'pointer',
              fontSize: 12, fontFamily: 'inherit',
            }}
          >
            Anterior
          </button>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
            Pagina {dir.page} de {dir.total_pages}
          </span>
          <button
            onClick={() => goToPage(dir.page + 1)}
            disabled={dir.page >= dir.total_pages}
            style={{
              padding: '6px 14px', borderRadius: 6,
              border: '1px solid var(--border)',
              background: dir.page >= dir.total_pages ? 'var(--bg-tertiary)' : 'var(--bg-secondary)',
              color: dir.page >= dir.total_pages ? 'var(--text-muted)' : 'var(--text-primary)',
              cursor: dir.page >= dir.total_pages ? 'not-allowed' : 'pointer',
              fontSize: 12, fontFamily: 'inherit',
            }}
          >
            Siguiente
          </button>
        </div>
      )}
    </DashboardCard>
  )
}

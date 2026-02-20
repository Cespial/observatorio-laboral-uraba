import { useEffect } from 'react'
import { useStore } from '../store'
import { SkeletonKPI, SkeletonChart } from './Skeleton'
import LaborSection from './dashboard/LaborSection'
import EconomySection from './dashboard/EconomySection'
import BusinessDirectory from './dashboard/BusinessDirectory'

function DashboardSkeleton() {
  return (
    <div className="dashboard-view">
      <div className="dashboard-grid">
        <div className="dashboard-card card" style={{ gridColumn: 'span 2' }}>
          <SkeletonKPI count={4} />
        </div>
        <div className="dashboard-card card">
          <SkeletonKPI count={4} />
        </div>
        <div className="dashboard-card card"><SkeletonChart /></div>
        <div className="dashboard-card card"><SkeletonChart /></div>
        <div className="dashboard-card card"><SkeletonChart /></div>
      </div>
    </div>
  )
}

export default function DashboardView() {
  const {
    selectedMunicipio,
    empleoData, empleoKpis, empleoAnalytics,
    economiaData, summary,
    fetchEmpleoKpis, fetchEmpleo, fetchEmpleoAnalytics,
    fetchEconomia,
  } = useStore()

  useEffect(() => {
    // Progressive data fetching
    fetchEmpleoKpis()
    fetchEmpleo()
    fetchEmpleoAnalytics()
    fetchEconomia()
  }, [selectedMunicipio])

  const hasLabor = empleoData || empleoKpis

  return (
    <div className="dashboard-view">
      <div style={{
        fontSize: 11, color: 'var(--text-muted)',
        marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.05em',
      }}>
        Tablero de Control — {selectedMunicipio}
      </div>

      {!hasLabor && !economiaData ? (
        <DashboardSkeleton />
      ) : (
        <div className="dashboard-grid">
          {/* Labor Section - spans 2 cols */}
          <div style={{ gridColumn: 'span 2', display: 'contents' }}>
            <LaborSection
              empleoData={empleoData}
              empleoKpis={empleoKpis}
              empleoAnalytics={empleoAnalytics}
            />
          </div>

          {/* Economy Section - spans 1 col */}
          <div style={{ display: 'contents' }}>
            <EconomySection
              economiaData={economiaData}
              summary={summary}
            />
          </div>

          {/* Business Directory - full width */}
          <BusinessDirectory />
        </div>
      )}
    </div>
  )
}

export { DashboardSkeleton }

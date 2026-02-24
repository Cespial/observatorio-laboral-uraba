import { useEffect } from 'react'
import { useStore } from '../store'
import { SkeletonKPI, SkeletonChart } from './Skeleton'
import LaborSection from './dashboard/LaborSection'
import EconomySection from './dashboard/EconomySection'
import BusinessDirectory from './dashboard/BusinessDirectory'
import InsightsBar from './dashboard/InsightsBar'
import EnrichmentCharts from './dashboard/EnrichmentCharts'
import OfertaDemandaGauge from './dashboard/OfertaDemandaGauge'
import SectorMunicipioHeatmap from './dashboard/SectorMunicipioHeatmap'
import OfertasExplorer from './dashboard/OfertasExplorer'
import CadenasProductivasSection from './dashboard/CadenasProductivasSection'
import EstacionalidadSection from './dashboard/EstacionalidadSection'
import InformalidadSection from './dashboard/InformalidadSection'

function DashboardSkeleton() {
  return (
    <div className="dashboard-view">
      <div className="dashboard-grid">
        <div className="dashboard-card card" style={{ gridColumn: 'span 3' }}>
          <SkeletonKPI count={3} />
        </div>
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
    enrichmentData, sectorMunicipioMatrix, ofertaDemandaData,
    cadenasProductivasData, estacionalidadData, informalidadData,
    salarioImputadoData,
    fetchEmpleoKpis, fetchEmpleo, fetchEmpleoAnalytics,
    fetchEconomia, fetchEnrichmentData,
    fetchSectorMunicipioMatrix, fetchOfertaDemanda,
    fetchCadenasProductivas, fetchEstacionalidad,
    fetchInformalidad, fetchSalarioImputado,
  } = useStore()

  useEffect(() => {
    // Progressive data fetching
    fetchEmpleoKpis()
    fetchEmpleo()
    fetchEmpleoAnalytics()
    fetchEnrichmentData()
    fetchSectorMunicipioMatrix()
    fetchOfertaDemanda()
    fetchEconomia()
    // Fase 2: deep labor analytics
    fetchCadenasProductivas()
    fetchEstacionalidad()
    fetchInformalidad()
    fetchSalarioImputado()
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
          {/* Row 1: Insights Bar (span 3) */}
          <InsightsBar
            empleoKpis={empleoKpis}
            empleoData={empleoData}
            enrichmentData={enrichmentData}
          />

          {/* Row 2: Labor KPIs (span 2) + Economy KPIs (span 1) */}
          <div style={{ gridColumn: 'span 2', display: 'contents' }}>
            <LaborSection
              empleoData={empleoData}
              empleoKpis={empleoKpis}
              empleoAnalytics={empleoAnalytics}
              salarioImputado={salarioImputadoData}
            />
          </div>
          <div style={{ display: 'contents' }}>
            <EconomySection
              economiaData={economiaData}
              summary={summary}
            />
          </div>

          {/* Row 3: Enrichment Charts (span 2) + Oferta-Demanda Gauge (span 1) */}
          <EnrichmentCharts enrichmentData={enrichmentData} />
          <OfertaDemandaGauge data={ofertaDemandaData} />

          {/* Row 4: Cadenas Productivas (span 2 + 1) */}
          <CadenasProductivasSection data={cadenasProductivasData} />

          {/* Row 5: Informalidad Laboral (span 2 + 1) */}
          <InformalidadSection data={informalidadData} />

          {/* Row 6: Estacionalidad Laboral (span 2 × 2) */}
          <EstacionalidadSection data={estacionalidadData} />

          {/* Row 7: Sector-Municipio Heatmap (span 2) */}
          <SectorMunicipioHeatmap data={sectorMunicipioMatrix} />

          {/* Row 8: Ofertas Explorer (span 3) */}
          <OfertasExplorer />

          {/* Row 9: Business Directory (span 3) */}
          <BusinessDirectory />
        </div>
      )}
    </div>
  )
}

export { DashboardSkeleton }

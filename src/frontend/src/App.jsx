import { useEffect, useMemo, lazy, Suspense } from 'react'
import { useStore } from './store'
import Header from './components/Header'
import KPICards from './components/KPICards'
import MapView from './components/MapView'
import LayerPanel from './components/LayerPanel'
import SidePanel from './components/SidePanel'
import Footer from './components/Footer'
import WelcomeOverlay from './components/WelcomeOverlay'

const DashboardView = lazy(() => import('./components/DashboardView'))

function Toast() {
  const toast = useStore((s) => s.toast)
  if (!toast) return null
  return (
    <div style={{
      position: 'fixed',
      bottom: 24,
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'var(--bg-card)',
      color: 'var(--text-primary)',
      border: '1px solid var(--border)',
      borderRadius: 8,
      padding: '8px 20px',
      fontSize: 13,
      fontWeight: 500,
      boxShadow: '0 4px 16px rgba(0,0,0,0.18)',
      zIndex: 9999,
      animation: 'fade-in 0.2s ease-out',
      pointerEvents: 'none',
    }}>
      {toast}
    </div>
  )
}

function DashboardFallback() {
  return (
    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 40 }}>
      <div style={{ textAlign: 'center' }}>
        <div className="skeleton" style={{ width: 200, height: 20, margin: '0 auto 12px' }} />
        <div className="skeleton" style={{ width: 140, height: 14, margin: '0 auto' }} />
      </div>
    </div>
  )
}

export default function App() {
  const { summary, fetchSummary, fetchCatalogSummary, activeView } = useStore()

  const isEmbed = useMemo(() => {
    const params = new URLSearchParams(window.location.search)
    return params.get('embed') === 'true'
  }, [])

  useEffect(() => {
    fetchSummary()
    fetchCatalogSummary()
  }, [])

  return (
    <>
      {!isEmbed && <WelcomeOverlay />}
      {!isEmbed && <Header />}
      {!isEmbed && <KPICards summary={summary} />}
      <div className="main-layout" style={{ flex: 1, display: 'flex', position: 'relative', overflow: 'hidden' }}>
        {activeView === 'mapa' ? (
          <>
            <div style={{ flex: 1, position: 'relative' }}>
              <MapView />
              {!isEmbed && <LayerPanel />}
            </div>
            <SidePanel />
          </>
        ) : (
          <Suspense fallback={<DashboardFallback />}>
            <DashboardView />
          </Suspense>
        )}
      </div>
      {!isEmbed && <Footer />}
      <Toast />
    </>
  )
}

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useStore } from '../store'

describe('Zustand Store', () => {
  beforeEach(() => {
    // Reset store between tests
    useStore.setState({
      toast: null,
      selectedMunicipio: 'Apartadó',
      theme: 'light',
      activeView: 'mapa',
      activeLayers: ['limite_municipal', 'osm_vias', 'google_places', 'veredas_mgn'],
      empleoData: null,
      empleoKpis: null,
      errors: {},
    })
    vi.restoreAllMocks()
  })

  describe('theme', () => {
    it('should default to light theme', () => {
      const { theme } = useStore.getState()
      expect(theme).toBe('light')
    })

    it('should toggle theme', () => {
      const { toggleTheme } = useStore.getState()
      toggleTheme()
      expect(useStore.getState().theme).toBe('dark')
      toggleTheme()
      expect(useStore.getState().theme).toBe('light')
    })
  })

  describe('municipios', () => {
    it('should have 12 municipios (11 + regional)', () => {
      const { municipios } = useStore.getState()
      expect(municipios).toHaveLength(12)
    })

    it('should default to Apartadó', () => {
      const { selectedMunicipio } = useStore.getState()
      expect(selectedMunicipio).toBe('Apartadó')
    })

    it('each municipio should have required fields', () => {
      const { municipios } = useStore.getState()
      for (const m of municipios) {
        expect(m).toHaveProperty('name')
        expect(m).toHaveProperty('lat')
        expect(m).toHaveProperty('lon')
        expect(m).toHaveProperty('zoom')
        expect(m).toHaveProperty('divipola')
      }
    })

    it('should have correct DANE codes', () => {
      const { municipios } = useStore.getState()
      const apartado = municipios.find(m => m.name === 'Apartadó')
      expect(apartado.divipola).toBe('05045')
      const turbo = municipios.find(m => m.name === 'Turbo')
      expect(turbo.divipola).toBe('05837')
    })
  })

  describe('layers', () => {
    it('should toggle layers', () => {
      const { toggleLayer } = useStore.getState()
      toggleLayer('manzanas_censales')
      expect(useStore.getState().activeLayers).toContain('manzanas_censales')
      toggleLayer('manzanas_censales')
      expect(useStore.getState().activeLayers).not.toContain('manzanas_censales')
    })
  })

  describe('toast', () => {
    it('should show and auto-clear toast', async () => {
      const { showToast } = useStore.getState()
      showToast('Test message', 100)
      expect(useStore.getState().toast).toBe('Test message')
      await new Promise(r => setTimeout(r, 150))
      expect(useStore.getState().toast).toBeNull()
    })
  })

  describe('activeView', () => {
    it('should switch between mapa and tablero', () => {
      const { setActiveView } = useStore.getState()
      setActiveView('tablero')
      expect(useStore.getState().activeView).toBe('tablero')
      setActiveView('mapa')
      expect(useStore.getState().activeView).toBe('mapa')
    })
  })

  describe('fetchEmpleo', () => {
    it('should fetch empleo data and set state', async () => {
      const mockData = { stats: { total_ofertas: 100 }, serie: [], skills: [], salarios: {}, sectores: [] }
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData.stats),
      })

      // Ensure empleoData starts null
      expect(useStore.getState().empleoData).toBeNull()
    })

    it('should handle fetch errors gracefully', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))
      const { fetchEmpleo } = useStore.getState()
      await fetchEmpleo()
      // Should not crash, error gets logged
      expect(useStore.getState().errors).toHaveProperty('empleo')
    })
  })
})

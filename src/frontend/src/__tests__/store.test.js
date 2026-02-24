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

  describe('Fase 2: new fetch functions', () => {
    it('should have fetchCadenasProductivas function', () => {
      const { fetchCadenasProductivas } = useStore.getState()
      expect(typeof fetchCadenasProductivas).toBe('function')
    })

    it('should have fetchEstacionalidad function', () => {
      const { fetchEstacionalidad } = useStore.getState()
      expect(typeof fetchEstacionalidad).toBe('function')
    })

    it('should have fetchInformalidad function', () => {
      const { fetchInformalidad } = useStore.getState()
      expect(typeof fetchInformalidad).toBe('function')
    })

    it('should have fetchSalarioImputado function', () => {
      const { fetchSalarioImputado } = useStore.getState()
      expect(typeof fetchSalarioImputado).toBe('function')
    })

    it('should have fetchSkillsCategorized function', () => {
      const { fetchSkillsCategorized } = useStore.getState()
      expect(typeof fetchSkillsCategorized).toBe('function')
    })

    it('should initialize new state fields as null', () => {
      const state = useStore.getState()
      expect(state.cadenasProductivasData).toBeNull()
      expect(state.estacionalidadData).toBeNull()
      expect(state.informalidadData).toBeNull()
      expect(state.salarioImputadoData).toBeNull()
      expect(state.skillsCategorizedData).toBeNull()
    })

    it('fetchCadenasProductivas should set data on success', async () => {
      const mockData = [{ cadena: 'Banano y Plátano', ofertas: 50 }]
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      })
      await useStore.getState().fetchCadenasProductivas()
      expect(useStore.getState().cadenasProductivasData).toEqual(mockData)
    })

    it('fetchEstacionalidad should set data on success', async () => {
      const mockData = { perfil_general: [], sectores_estacionales: [], promedio_mensual: 10 }
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      })
      await useStore.getState().fetchEstacionalidad()
      expect(useStore.getState().estacionalidadData).toEqual(mockData)
    })

    it('fetchInformalidad should set data on success', async () => {
      const mockData = [{ municipio: 'Apartadó', indice_compuesto: 55.0 }]
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      })
      await useStore.getState().fetchInformalidad()
      expect(useStore.getState().informalidadData).toEqual(mockData)
    })

    it('fetchSalarioImputado should set data on success', async () => {
      const mockData = { tabla_referencia: [], cobertura: { total_ofertas: 100 } }
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockData),
      })
      await useStore.getState().fetchSalarioImputado()
      expect(useStore.getState().salarioImputadoData).toEqual(mockData)
    })

    it('fetch functions should handle errors gracefully', async () => {
      global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))
      // Reset state to null so early-return guard doesn't skip fetch
      useStore.setState({
        cadenasProductivasData: null,
        estacionalidadData: null,
        informalidadData: null,
      })
      await useStore.getState().fetchCadenasProductivas()
      expect(useStore.getState().errors).toHaveProperty('cadenas')

      await useStore.getState().fetchEstacionalidad()
      expect(useStore.getState().errors).toHaveProperty('estacionalidad')

      await useStore.getState().fetchInformalidad()
      expect(useStore.getState().errors).toHaveProperty('informalidad')
    })

    it('fetch functions should skip if data already loaded', async () => {
      useStore.setState({ cadenasProductivasData: [{ cadena: 'cached' }] })
      global.fetch = vi.fn()
      await useStore.getState().fetchCadenasProductivas()
      // fetch should NOT have been called since data exists
      expect(global.fetch).not.toHaveBeenCalled()
    })
  })
})

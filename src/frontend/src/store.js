import { create } from 'zustand'
import { FlyToInterpolator } from '@deck.gl/core'

const API = '/api'

const savedTheme = typeof window !== 'undefined'
  ? localStorage.getItem('observatorio-theme') || 'light'
  : 'light'
if (typeof document !== 'undefined') {
  document.documentElement.setAttribute('data-theme', savedTheme)
}

async function safeFetch(url) {
  const r = await fetch(url)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

export const useStore = create((set, get) => ({
  toast: null,
  showToast: (message, duration = 2500) => {
    set({ toast: message })
    setTimeout(() => set({ toast: null }), duration)
  },

  catalogSummary: null,
  fetchCatalogSummary: async () => {
    if (get().catalogSummary) return
    try {
      set({ catalogSummary: await safeFetch(`${API}/stats/catalog-summary`) })
    } catch (e) {
      console.error('fetchCatalogSummary:', e)
    }
  },

  theme: savedTheme,
  toggleTheme: () => {
    const next = get().theme === 'light' ? 'dark' : 'light'
    document.documentElement.setAttribute('data-theme', next)
    localStorage.setItem('observatorio-theme', next)
    set({ theme: next })
  },

  viewState: {
    longitude: -76.6258,
    latitude: 7.8833,
    zoom: 13,
    pitch: 45,
    bearing: -15,
  },
  setViewState: (vs) => set({ viewState: vs }),

  selectedMunicipio: 'Apartadó',
  municipios: [
    { name: 'Apartadó', lat: 7.8833, lon: -76.6258, zoom: 13, divipola: '05045' },
    { name: 'Turbo', lat: 8.0933, lon: -76.7297, zoom: 12, divipola: '05837' },
    { name: 'Carepa', lat: 7.7583, lon: -76.6583, zoom: 13, divipola: '05147' },
    { name: 'Chigorodó', lat: 7.6667, lon: -76.6833, zoom: 13, divipola: '05172' },
    { name: 'Necoclí', lat: 8.4233, lon: -76.7858, zoom: 13, divipola: '05490' },
    { name: 'San Pedro de Urabá', lat: 8.2753, lon: -76.3764, zoom: 13, divipola: '05665' },
    { name: 'San Juan de Urabá', lat: 8.7592, lon: -76.5297, zoom: 13, divipola: '05659' },
    { name: 'Arboletes', lat: 8.8503, lon: -76.4269, zoom: 13, divipola: '05051' },
    { name: 'Mutatá', lat: 7.2453, lon: -76.4358, zoom: 13, divipola: '05480' },
    { name: 'Murindó', lat: 6.8867, lon: -76.7533, zoom: 12, divipola: '05475' },
    { name: 'Vigía del Fuerte', lat: 6.5892, lon: -76.8906, zoom: 12, divipola: '05873' },
    { name: 'Urabá (Regional)', lat: 8.2, lon: -76.6, zoom: 8.5, divipola: 'REGIONAL' },
  ],

  setSelectedMunicipio: (name) => {
    const mun = get().municipios.find(m => m.name === name)
    if (mun) {
      set({
        selectedMunicipio: name,
        activePanel: name === 'Urabá (Regional)' ? 'comparative' : 'overview',
        viewState: {
          ...get().viewState,
          latitude: mun.lat,
          longitude: mun.lon,
          zoom: mun.zoom,
          pitch: name === 'Urabá (Regional)' ? 0 : 45,
          bearing: name === 'Urabá (Regional)' ? 0 : -15,
          transitionDuration: 2000,
          transitionInterpolator: new FlyToInterpolator(),
        }
      })
      
      // Trigger refetch of geo layers for the new context
      const { fetchManzanas, fetchPlaces, fetchLayerGeoJSON, activeLayers } = get()
      
      // Clear cached data so it refetches for the new municipality
      set((s) => ({
        layerData: {},
        securityMatrix: null,
        icfesData: null,
        victimasData: null,
        saludData: null,
        economiaData: null,
        gobiernoData: null,
        culturaData: null,
        crossvarVariables: null,
        empleoData: null,
        empleoKpis: null,
        empleoAnalytics: null,
        businessDirectory: null,
        errors: {},
      }))

      // Re-fetch standard layers
      fetchManzanas()
      fetchPlaces()
      
      // Re-fetch any other active layers
      activeLayers.forEach(id => {
        if (id !== 'manzanas_censales' && id !== 'google_places' && id !== 'places_heatmap') {
           fetchLayerGeoJSON(id)
        }
      })

      // Fetch summary for the new context
      get().fetchSummary(mun.divipola !== 'REGIONAL' ? mun.divipola : null)
      
      get().showToast(`Cambiando a vista: ${name}`)
    }
  },

  activeLayers: ['limite_municipal', 'osm_vias', 'google_places', 'veredas_mgn'],
  toggleLayer: (id) => set((s) => ({
    activeLayers: s.activeLayers.includes(id)
      ? s.activeLayers.filter((l) => l !== id)
      : [...s.activeLayers, id],
  })),

  layerData: {},
  summary: null,
  securityMatrix: null,
  placesCategories: null,
  icfesData: null,
  victimasData: null,
  crossvarData: null,
  saludData: null,
  economiaData: null,
  gobiernoData: null,
  culturaData: null,
  crossvarVariables: null,
  empleoData: null,
  empleoKpis: null,
  empleoAnalytics: null,
  errors: {},
  selectedCategory: null,
  setSelectedCategory: (cat) => set({ selectedCategory: cat }),
  activeView: 'mapa',
  setActiveView: (v) => set({ activeView: v }),
  businessDirectory: null,
  businessDirectoryLoading: false,
  businessDirectoryParams: { page: 1, search: '', category: null, min_rating: 0 },
  activePanel: 'overview',
  setActivePanel: (p) => set({ activePanel: p }),

  fetchSummary: async (daneCode = null) => {
    const param = daneCode ? `?dane_code=${daneCode}` : ''
    try {
      const data = await safeFetch(`${API}/stats/summary${param}`)
      set({ summary: data })
    } catch (e) {
      console.error('fetchSummary:', e)
      set((s) => ({ 
        errors: { ...s.errors, summary: e.message },
        summary: { municipio: 'Error', region: 'Urabá', divipola: daneCode || '---' } 
      }))
    }
  },
  municipioCentroids: null,
  fetchCentroids: async () => {
    if (get().municipioCentroids) return
    try {
      set({ municipioCentroids: await safeFetch(`${API}/geo/municipios/centroids`) })
    } catch (e) {
      console.error('fetchCentroids:', e)
    }
  },
  fetchLayerGeoJSON: async (id) => {
    // limite_municipal always loads ALL 11 municipalities (no dane_code filter)
    const skipDaneFilter = ['limite_municipal', 'igac_uraba']
    const municipio = get().selectedMunicipio
    const mun = get().municipios.find(m => m.name === municipio)
    const daneParam = !skipDaneFilter.includes(id) && mun && mun.divipola !== 'REGIONAL'
      ? `?dane_code=${mun.divipola}`
      : ''

    try {
      const d = await safeFetch(`${API}/layers/${id}/geojson${daneParam}`)
      set((s) => ({ layerData: { ...s.layerData, [id]: d } }))
    } catch (e) {
      console.error(`fetchLayer(${id}):`, e)
    }
  },
  fetchVeredas: async () => {
    const municipio = get().selectedMunicipio
    const mun = get().municipios.find(m => m.name === municipio)
    const daneParam = mun && mun.divipola !== 'REGIONAL' ? `?dane_code=${mun.divipola}` : ''
    try {
      const d = await safeFetch(`${API}/layers/veredas_mgn/geojson${daneParam}`)
      set((s) => ({ layerData: { ...s.layerData, veredas_mgn: d } }))
    } catch (e) {
      console.error('fetchVeredas:', e)
    }
  },
  fetchManzanas: async () => {
    // Always re-fetch when called, to match selected municipality
    const municipio = get().selectedMunicipio
    const mun = get().municipios.find(m => m.name === municipio)
    const daneParam = mun && mun.divipola !== 'REGIONAL' ? `&dane_code=${mun.divipola}` : ''

    try {
      const d = await safeFetch(`${API}/geo/manzanas?limit=5000${daneParam}`)
      set((s) => ({ layerData: { ...s.layerData, manzanas: d } }))
    } catch (e) {
      console.error('fetchManzanas:', e)
    }
  },
  fetchPlaces: async () => {
    const municipio = get().selectedMunicipio
    const mun = get().municipios.find(m => m.name === municipio)
    const daneParam = mun && mun.divipola !== 'REGIONAL' ? `&dane_code=${mun.divipola}` : ''

    try {
      const [pData, cData] = await Promise.all([
        safeFetch(`${API}/geo/places?limit=2000${daneParam}`),
        safeFetch(`${API}/geo/places/categories`),
      ])
      set((s) => ({
        layerData: { ...s.layerData, places: pData },
        placesCategories: cData,
      }))
    } catch (e) {
      console.error('fetchPlaces:', e)
    }
  },
  fetchPlacesHeatmap: async () => {
    if (get().layerData.placesHeatmap) return
    try {
      const d = await safeFetch(`${API}/geo/places/heatmap`)
      set((s) => ({ layerData: { ...s.layerData, placesHeatmap: d } }))
    } catch (e) {
      console.error('fetchPlacesHeatmap:', e)
    }
  },
  fetchSecurityMatrix: async () => {
    if (get().securityMatrix) return
    try {
      const d = await safeFetch(`${API}/crossvar/security-matrix`)
      set({ securityMatrix: d.data })
    } catch (e) {
      console.error('fetchSecurityMatrix:', e)
      set((s) => ({ errors: { ...s.errors, seguridad: e.message } }))
    }
  },
  fetchIcfes: async () => {
    if (get().icfesData) return
    try {
      set({ icfesData: await safeFetch(`${API}/indicators/icfes?aggregate=periodo`) })
    } catch (e) {
      console.error('fetchIcfes:', e)
      set((s) => ({ errors: { ...s.errors, educacion: e.message } }))
    }
  },
  fetchVictimas: async () => {
    if (get().victimasData) return
    try {
      set({ victimasData: await safeFetch(`${API}/indicators/victimas?aggregate=hecho`) })
    } catch (e) {
      console.error('fetchVictimas:', e)
      set((s) => ({ errors: { ...s.errors, victimas: e.message } }))
    }
  },
  fetchCrossvar: async (vx, vy) => {
    try {
      set({ crossvarData: await safeFetch(`${API}/crossvar/scatter?var_x=${vx}&var_y=${vy}`) })
    } catch (e) {
      console.error('fetchCrossvar:', e)
      set((s) => ({ errors: { ...s.errors, cruces: e.message } }))
    }
  },
  fetchSalud: async () => {
    if (get().saludData) return
    try {
      const [td, ir, sv] = await Promise.all([
        safeFetch(`${API}/indicators/terridata?dimension=Salud`),
        safeFetch(`${API}/indicators/salud/irca`),
        safeFetch(`${API}/indicators/salud/sivigila/resumen`),
      ])
      set({ saludData: { terridata: td, irca: ir, sivigila: sv } })
    } catch (e) {
      console.error('fetchSalud:', e)
      set((s) => ({ errors: { ...s.errors, salud: e.message } }))
    }
  },
  fetchEconomia: async () => {
    if (get().economiaData) return
    const mun = get().municipios.find(m => m.name === get().selectedMunicipio)
    const dp = mun && mun.divipola !== 'REGIONAL' ? `dane_code=${mun.divipola}` : ''
    const sep = dp ? '&' : ''
    try {
      const [inet, sec, tur, td] = await Promise.all([
        safeFetch(`${API}/indicators/economia/internet/serie${dp ? '?' + dp : ''}`),
        safeFetch(`${API}/indicators/economia/secop${dp ? '?' + dp : ''}`),
        safeFetch(`${API}/indicators/economia/turismo${dp ? '?' + dp : ''}`),
        safeFetch(`${API}/indicators/terridata?dimension=${encodeURIComponent('Economía')}${sep}${dp}`),
      ])
      set({
        economiaData: {
          internet: inet,
          secop: sec,
          turismo: tur,
          terridata_economia: td,
        },
      })
    } catch (e) {
      console.error('fetchEconomia:', e)
      set((s) => ({ errors: { ...s.errors, economia: e.message } }))
    }
  },
  fetchGobierno: async () => {
    if (get().gobiernoData) return
    try {
      const [fin, des, dig, pob] = await Promise.all([
        safeFetch(`${API}/indicators/gobierno/finanzas`),
        safeFetch(`${API}/indicators/gobierno/desempeno`),
        safeFetch(`${API}/indicators/gobierno/digital`),
        safeFetch(`${API}/indicators/gobierno/pobreza`),
      ])
      set({
        gobiernoData: {
          finanzas: fin,
          desempeno: des,
          digital: dig,
          pobreza: pob,
        },
      })
    } catch (e) {
      console.error('fetchGobierno:', e)
      set((s) => ({ errors: { ...s.errors, gobierno: e.message } }))
    }
  },
  fetchCultura: async () => {
    if (get().culturaData) return
    try {
      const [espacios, turismo] = await Promise.all([
        safeFetch(`${API}/indicators/cultura/espacios`),
        safeFetch(`${API}/indicators/cultura/turismo-detalle`),
      ])
      set({ culturaData: { espacios, turismo } })
    } catch (e) {
      console.error('fetchCultura:', e)
      set((s) => ({ errors: { ...s.errors, cultura: e.message } }))
    }
  },
  fetchCrossvarVariables: async () => {
    if (get().crossvarVariables) return
    try {
      set({ crossvarVariables: await safeFetch(`${API}/crossvar/variables`) })
    } catch (e) {
      console.error('fetchCrossvarVariables:', e)
    }
  },
  fetchEmpleo: async () => {
    if (get().empleoData) return
    const mun = get().municipios.find(m => m.name === get().selectedMunicipio)
    const dp = mun && mun.divipola !== 'REGIONAL' ? `?dane_code=${mun.divipola}` : ''
    try {
      const [stats, serie, skills, salarios, sectores] = await Promise.all([
        safeFetch(`${API}/empleo/stats${dp}`),
        safeFetch(`${API}/empleo/serie-temporal${dp}`),
        safeFetch(`${API}/empleo/skills${dp}`),
        safeFetch(`${API}/empleo/salarios${dp}`),
        safeFetch(`${API}/empleo/sectores${dp}`),
      ])
      set({ empleoData: { stats, serie, skills, salarios, sectores } })
    } catch (e) {
      console.error('fetchEmpleo:', e)
      set((s) => ({ errors: { ...s.errors, empleo: e.message } }))
    }
  },
  fetchEmpleoKpis: async () => {
    if (get().empleoKpis) return
    const mun = get().municipios.find(m => m.name === get().selectedMunicipio)
    const dp = mun && mun.divipola !== 'REGIONAL' ? `?dane_code=${mun.divipola}` : ''
    try {
      set({ empleoKpis: await safeFetch(`${API}/empleo/kpis${dp}`) })
    } catch (e) {
      console.error('fetchEmpleoKpis:', e)
    }
  },
  fetchEmpleoAnalytics: async () => {
    if (get().empleoAnalytics) return
    const mun = get().municipios.find(m => m.name === get().selectedMunicipio)
    const dp = mun && mun.divipola !== 'REGIONAL' ? `?dane_code=${mun.divipola}` : ''
    try {
      const [termometro, dinamismo, concentracion, brechaSkills] = await Promise.all([
        safeFetch(`${API}/analytics/laboral/termometro${dp}`),
        safeFetch(`${API}/analytics/laboral/dinamismo${dp}`),
        safeFetch(`${API}/analytics/laboral/concentracion${dp}`),
        safeFetch(`${API}/analytics/laboral/brecha-skills${dp}`),
      ])
      set({ empleoAnalytics: { termometro, dinamismo, concentracion, brechaSkills } })
    } catch (e) {
      console.error('fetchEmpleoAnalytics:', e)
      set((s) => ({ errors: { ...s.errors, empleoAnalytics: e.message } }))
    }
  },
  fetchBusinessDirectory: async (params = {}) => {
    const mun = get().municipios.find(m => m.name === get().selectedMunicipio)
    const dane = mun && mun.divipola !== 'REGIONAL' ? mun.divipola : ''
    const merged = { ...get().businessDirectoryParams, ...params }
    set({ businessDirectoryLoading: true, businessDirectoryParams: merged })
    const qs = new URLSearchParams()
    if (dane) qs.set('dane_code', dane)
    if (merged.search) qs.set('search', merged.search)
    if (merged.category) qs.set('category', merged.category)
    if (merged.min_rating > 0) qs.set('min_rating', String(merged.min_rating))
    qs.set('page', String(merged.page || 1))
    qs.set('page_size', '25')
    try {
      const data = await safeFetch(`${API}/geo/places/directory?${qs}`)
      set({ businessDirectory: data, businessDirectoryLoading: false })
    } catch (e) {
      console.error('fetchBusinessDirectory:', e)
      set({ businessDirectoryLoading: false })
    }
  },
}))

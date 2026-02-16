import { create } from 'zustand'

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

  activeLayers: ['limite_municipal', 'osm_vias', 'google_places'],
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
  errors: {},
  selectedCategory: null,
  setSelectedCategory: (cat) => set({ selectedCategory: cat }),
  activePanel: 'overview',
  setActivePanel: (p) => set({ activePanel: p }),

  fetchSummary: async () => {
    try {
      set({ summary: await safeFetch(`${API}/stats/summary`) })
    } catch (e) {
      console.error('fetchSummary:', e)
      set((s) => ({ errors: { ...s.errors, summary: e.message } }))
    }
  },
  fetchLayerGeoJSON: async (id) => {
    if (get().layerData[id]) return
    try {
      const d = await safeFetch(`${API}/layers/${id}/geojson`)
      set((s) => ({ layerData: { ...s.layerData, [id]: d } }))
    } catch (e) {
      console.error(`fetchLayer(${id}):`, e)
    }
  },
  fetchManzanas: async () => {
    if (get().layerData.manzanas) return
    try {
      const d = await safeFetch(`${API}/geo/manzanas?limit=5000`)
      set((s) => ({ layerData: { ...s.layerData, manzanas: d } }))
    } catch (e) {
      console.error('fetchManzanas:', e)
    }
  },
  fetchPlaces: async () => {
    if (get().layerData.places) return
    try {
      const [pData, cData] = await Promise.all([
        safeFetch(`${API}/geo/places?limit=2000`),
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
    try {
      const [inet, sec, tur, td] = await Promise.all([
        safeFetch(`${API}/indicators/economia/internet/serie`),
        safeFetch(`${API}/indicators/economia/secop`),
        safeFetch(`${API}/indicators/economia/turismo`),
        safeFetch(`${API}/indicators/terridata?dimension=${encodeURIComponent('Economía')}`),
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
}))

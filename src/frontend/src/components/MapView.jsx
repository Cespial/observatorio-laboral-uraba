import { useEffect, useCallback, useMemo, useState } from 'react'
import { Map } from 'react-map-gl/maplibre'
import DeckGL from '@deck.gl/react'
import { FlyToInterpolator } from '@deck.gl/core'
import { GeoJsonLayer, ScatterplotLayer, TextLayer } from '@deck.gl/layers'
import { HeatmapLayer } from '@deck.gl/aggregation-layers'
import { useStore } from '../store'

// Free basemaps compatible with MapLibre (no token required)
const MAP_STYLES = {
  light: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
  dark: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
}
const MAP_STYLE = MAP_STYLES.light

const CATEGORY_COLORS = {
  'school': [24, 144, 255],
  'pharmacy': [82, 196, 26],
  'bank': [0, 80, 179],
  'supermarket': [64, 169, 255],
  'gas_station': [250, 140, 22],
  'hospital': [245, 34, 45],
  'local_government_office': [140, 140, 140],
  'atm': [105, 192, 255],
  'police': [207, 19, 34],
}

const DEFAULT_COLOR = [24, 144, 255]

function getCategoryColor(category) {
  return CATEGORY_COLORS[category] || DEFAULT_COLOR
}

function getPopulationColor(totalPersonas) {
  const maxPop = 500
  const t = Math.min(totalPersonas / maxPop, 1)
  return [
    Math.round(145 * (1 - t) + 0 * t),
    Math.round(213 * (1 - t) + 80 * t),
    Math.round(255 * (1 - t) + 179 * t),
  ]
}

export default function MapView() {
  const [popup, setPopup] = useState(null)
  const viewState = useStore((s) => s.viewState)
  const setViewState = useStore((s) => s.setViewState)
  const activeLayers = useStore((s) => s.activeLayers)
  const layerData = useStore((s) => s.layerData)
  const fetchLayerGeoJSON = useStore((s) => s.fetchLayerGeoJSON)
  const fetchManzanas = useStore((s) => s.fetchManzanas)
  const fetchVeredas = useStore((s) => s.fetchVeredas)
  const fetchPlaces = useStore((s) => s.fetchPlaces)
  const fetchPlacesHeatmap = useStore((s) => s.fetchPlacesHeatmap)
  const selectedCategory = useStore((s) => s.selectedCategory)
  const selectedMunicipio = useStore((s) => s.selectedMunicipio)
  const municipios = useStore((s) => s.municipios)
  const municipioCentroids = useStore((s) => s.municipioCentroids)
  const fetchCentroids = useStore((s) => s.fetchCentroids)
  const empleoAnalytics = useStore((s) => s.empleoAnalytics)
  const fetchEmpleoAnalytics = useStore((s) => s.fetchEmpleoAnalytics)

  useEffect(() => {
    fetchLayerGeoJSON('limite_municipal')
    fetchManzanas()
    fetchVeredas()
    fetchPlaces()
    fetchPlacesHeatmap()
    fetchCentroids()
    fetchEmpleoAnalytics()
  }, [fetchLayerGeoJSON, fetchManzanas, fetchVeredas, fetchPlaces, fetchPlacesHeatmap, fetchCentroids, fetchEmpleoAnalytics])

  const onViewStateChange = useCallback(
    ({ viewState: vs }) => {
      setViewState(vs)
      setPopup(null)
    },
    [setViewState],
  )

  const layers = useMemo(() => {
    const result = []

    if (activeLayers.includes('limite_municipal') && layerData.limite_municipal) {
      const selDivipola = municipios.find(m => m.name === selectedMunicipio)?.divipola
      result.push(
        new GeoJsonLayer({
          id: 'limite_municipal',
          data: layerData.limite_municipal,
          filled: true,
          stroked: true,
          getFillColor: (f) => {
            const code = f.properties.dane_code
            return code === selDivipola ? [0, 80, 179, 40] : [0, 80, 179, 10]
          },
          getLineColor: [0, 50, 140],
          getLineWidth: 3,
          lineWidthUnits: 'pixels',
          pickable: true,
          updateTriggers: {
            getFillColor: [selDivipola],
          },
        }),
      )

      // Municipality name labels
      if (municipioCentroids && municipioCentroids.length > 0) {
        result.push(
          new TextLayer({
            id: 'municipio_labels',
            data: municipioCentroids,
            getPosition: (d) => [d.lon, d.lat],
            getText: (d) => d.nombre,
            getSize: 14,
            getColor: [0, 30, 80, 220],
            getTextAnchor: 'middle',
            getAlignmentBaseline: 'center',
            fontWeight: 'bold',
            outlineWidth: 2,
            outlineColor: [255, 255, 255, 200],
            fontFamily: 'system-ui, sans-serif',
            sizeUnits: 'pixels',
            billboard: false,
          }),
        )
      }
    }

    if (activeLayers.includes('veredas_mgn') && layerData.veredas_mgn) {
      result.push(
        new GeoJsonLayer({
          id: 'veredas_mgn',
          data: layerData.veredas_mgn,
          filled: true,
          stroked: true,
          getFillColor: [0, 120, 255, 20],
          getLineColor: [0, 80, 179, 100],
          getLineWidth: 1,
          lineWidthUnits: 'pixels',
          pickable: true,
        }),
      )
    }

    if (activeLayers.includes('osm_edificaciones') && layerData.osm_edificaciones && viewState.zoom > 14) {
      result.push(
        new GeoJsonLayer({
          id: 'osm_edificaciones',
          data: layerData.osm_edificaciones,
          filled: true,
          stroked: false,
          getFillColor: [94, 102, 135],
          opacity: 0.3,
        }),
      )
    }

    if (activeLayers.includes('osm_vias') && layerData.osm_vias) {
      result.push(
        new GeoJsonLayer({
          id: 'osm_vias',
          data: layerData.osm_vias,
          filled: false,
          stroked: true,
          getLineColor: [0, 80, 179],
          opacity: 0.4,
          getLineWidth: 1,
          lineWidthUnits: 'pixels',
        }),
      )
    }

    if (activeLayers.includes('manzanas_censales') && layerData.manzanas && viewState.zoom > 11) {
      result.push(
        new GeoJsonLayer({
          id: 'manzanas_censales',
          data: layerData.manzanas,
          filled: true,
          stroked: false,
          extruded: true,
          wireframe: false,
          opacity: 0.7,
          getElevation: (f) => {
            const pop = parseInt(f.properties.total_personas, 10) || 0
            return pop * 3
          },
          getFillColor: (f) => {
            const pop = parseInt(f.properties.total_personas, 10) || 0
            return getPopulationColor(pop)
          },
          pickable: true,
          material: {
            ambient: 0.4,
            diffuse: 0.6,
            shininess: 32,
          },
        }),
      )
    }

    if (activeLayers.includes('google_places') && layerData.places) {
      const allFeatures = layerData.places.features || []
      const features = selectedCategory
        ? allFeatures.filter((f) => f.properties.category === selectedCategory)
        : allFeatures
      result.push(
        new ScatterplotLayer({
          id: 'google_places',
          data: features,
          getPosition: (f) => f.geometry.coordinates,
          getRadius: 40,
          radiusUnits: 'meters',
          getFillColor: (f) => getCategoryColor(f.properties.category),
          pickable: true,
        }),
      )
    }

    if (activeLayers.includes('places_heatmap') && layerData.placesHeatmap) {
      const heatData = layerData.placesHeatmap
      result.push(
        new HeatmapLayer({
          id: 'places_heatmap',
          data: heatData,
          getPosition: (d) => [d.lon, d.lat],
          getWeight: (d) => d.weight || 1,
          radiusPixels: 60,
          colorRange: [
            [198, 219, 239, 25],
            [158, 202, 225, 100],
            [107, 174, 214, 180],
            [66, 146, 198, 220],
            [33, 113, 181, 240],
            [8, 69, 148, 255],
          ],
          intensity: 1,
          threshold: 0.05,
        }),
      )
    }

    // Employment concentration bubbles
    if (activeLayers.includes('empleo_concentracion') && empleoAnalytics?.concentracion) {
      const empData = empleoAnalytics.concentracion.filter(c => c.lat && c.lon)
      const maxOfertas = Math.max(...empData.map(c => c.ofertas || 0), 1)
      result.push(
        new ScatterplotLayer({
          id: 'empleo_concentracion',
          data: empData,
          getPosition: (d) => [d.lon, d.lat],
          getRadius: (d) => Math.max(800, Math.sqrt((d.ofertas || 0) / maxOfertas) * 5000),
          radiusUnits: 'meters',
          getFillColor: [250, 140, 22, 160],
          getLineColor: [200, 100, 0, 200],
          stroked: true,
          lineWidthMinPixels: 1.5,
          pickable: true,
        }),
      )
      // Employment bubble labels
      result.push(
        new TextLayer({
          id: 'empleo_labels',
          data: empData,
          getPosition: (d) => [d.lon, d.lat],
          getText: (d) => `${d.ofertas}`,
          getSize: 12,
          getColor: [120, 60, 0, 255],
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'center',
          fontWeight: 'bold',
          outlineWidth: 2,
          outlineColor: [255, 255, 255, 220],
          fontFamily: 'system-ui, sans-serif',
          sizeUnits: 'pixels',
          billboard: false,
        }),
      )
    }

    return result
  }, [activeLayers, layerData, selectedCategory, viewState.zoom, selectedMunicipio, municipios, municipioCentroids, empleoAnalytics])

  const onClick = useCallback((info) => {
    if (!info.object) { setPopup(null); return }
    const props = info.object.properties || info.object
    const [lng, lat] = info.coordinate || []
    if (props.name || props.category) {
      setPopup({ type: 'place', props, x: info.x, y: info.y, lng, lat })
    } else if (props.cod_dane_manzana) {
      setPopup({ type: 'manzana', props, x: info.x, y: info.y, lng, lat })
    }
  }, [])

  const getTooltip = useCallback(({ object }) => {
    if (!object) return null
    const props = object.properties || object
    if (props.nombre && props.dane_code) {
      return { text: `${props.nombre} (${props.dane_code})` }
    }
    if (props.ofertas && props.empresas && props.pct_ofertas != null) {
      return { text: `${props.municipio}\n${props.ofertas} vacantes · ${props.empresas} empresas` }
    }
    if (props.name) return { text: props.name }
    if (props.cod_dane_manzana) {
      const pop = parseInt(props.total_personas, 10) || 0
      return { text: `Manzana · ${pop} hab.` }
    }
    return null
  }, [])

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <DeckGL
        viewState={viewState}
        onViewStateChange={onViewStateChange}
        controller={true}
        layers={layers}
        getTooltip={getTooltip}
        onClick={onClick}
      >
        <Map
          mapStyle={MAP_STYLE}
          reuseMaps
        />
      </DeckGL>

      {popup && (() => {
        const pw = 280, ph = 160, margin = 12
        const flipX = popup.x + pw + margin > window.innerWidth
        const flipY = popup.y - ph - margin < 0
        const left = flipX ? popup.x - pw - margin : popup.x + margin
        const top = flipY ? popup.y + margin : popup.y - margin
        return (
        <div
          style={{
            position: 'absolute',
            left,
            top,
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: '10px 14px',
            fontSize: 12,
            color: 'var(--text-primary)',
            maxWidth: pw,
            boxShadow: '0 4px 16px rgba(0,0,0,0.18)',
            zIndex: 20,
            pointerEvents: 'auto',
          }}
        >
          <button
            onClick={() => setPopup(null)}
            aria-label="Cerrar popup"
            style={{
              position: 'absolute', top: 4, right: 8,
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: 14, color: 'var(--text-muted)', lineHeight: 1,
            }}
          >&times;</button>

          {popup.type === 'place' && (
            <>
              <div style={{ fontWeight: 700, color: 'var(--accent-primary)', marginBottom: 4, paddingRight: 16 }}>
                {popup.props.name}
              </div>
              {popup.props.category && (
                <div style={{ marginBottom: 2 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Categoria: </span>
                  <span className="badge badge-blue">{popup.props.category}</span>
                </div>
              )}
              {popup.props.rating != null && (
                <div style={{ marginBottom: 2 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Rating: </span>
                  <strong>{popup.props.rating}</strong>
                  <span style={{ color: 'var(--text-muted)', marginLeft: 4 }}>
                    ({popup.props.user_ratings_total || 0} resenas)
                  </span>
                </div>
              )}
              {popup.props.address && (
                <div style={{ color: 'var(--text-muted)', fontSize: 11, marginTop: 4 }}>
                  {popup.props.address}
                </div>
              )}
            </>
          )}

          {popup.type === 'manzana' && (
            <>
              <div style={{ fontWeight: 700, color: 'var(--accent-primary)', marginBottom: 4 }}>
                Manzana Censal
              </div>
              <div style={{ marginBottom: 2 }}>
                <span style={{ color: 'var(--text-secondary)' }}>DANE: </span>
                <span className="font-mono" style={{ fontSize: 11 }}>{popup.props.cod_dane_manzana}</span>
              </div>
              <div>
                <span style={{ color: 'var(--text-secondary)' }}>Poblacion: </span>
                <strong>{parseInt(popup.props.total_personas, 10) || 'N/D'}</strong>
                <span style={{ color: 'var(--text-muted)' }}> hab.</span>
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: 10, marginTop: 4 }}>
                Municipio: {popup.props.cod_dane_municipio}
              </div>
            </>
          )}
        </div>
        )
      })()}
    </div>
  )
}

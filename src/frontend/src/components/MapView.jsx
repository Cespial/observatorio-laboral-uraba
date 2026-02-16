import { useEffect, useCallback, useMemo, useState } from 'react'
import { Map } from 'react-map-gl/maplibre'
import DeckGL from '@deck.gl/react'
import { GeoJsonLayer, ScatterplotLayer } from '@deck.gl/layers'
import { HeatmapLayer } from '@deck.gl/aggregation-layers'
import { useStore } from '../store'

const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'

const CATEGORY_COLORS = {
  'Restaurantes': [250, 140, 22],
  'Bancos': [0, 80, 179],
  'Farmacias': [82, 196, 26],
  'Hospitales': [245, 34, 45],
  'Colegios': [24, 144, 255],
  'Supermercados': [64, 169, 255],
  'Tiendas': [105, 192, 255],
  'Iglesias': [140, 140, 140],
  'Hoteles': [250, 140, 22],
  'Caféterías': [160, 120, 60],
  'Bares': [207, 19, 34],
  'Panaderías': [212, 107, 8],
  'Ferreterías': [89, 89, 89],
  'Talleres mecánicos': [89, 89, 89],
  'Salones de belleza': [194, 84, 148],
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
  const fetchPlaces = useStore((s) => s.fetchPlaces)
  const fetchPlacesHeatmap = useStore((s) => s.fetchPlacesHeatmap)
  const selectedCategory = useStore((s) => s.selectedCategory)

  useEffect(() => {
    fetchLayerGeoJSON('limite_municipal')
    fetchLayerGeoJSON('osm_edificaciones')
    fetchLayerGeoJSON('osm_vias')
    fetchManzanas()
    fetchPlaces()
    fetchPlacesHeatmap()
  }, [fetchLayerGeoJSON, fetchManzanas, fetchPlaces, fetchPlacesHeatmap])

  const onViewStateChange = useCallback(
    ({ viewState: vs }) => setViewState(vs),
    [setViewState],
  )

  const layers = useMemo(() => {
    const result = []

    if (activeLayers.includes('limite_municipal') && layerData.limite_municipal) {
      result.push(
        new GeoJsonLayer({
          id: 'limite_municipal',
          data: layerData.limite_municipal,
          filled: false,
          stroked: true,
          getLineColor: [0, 80, 179],
          getLineWidth: 2.5,
          lineWidthUnits: 'pixels',
        }),
      )
    }

    if (activeLayers.includes('osm_edificaciones') && layerData.osm_edificaciones) {
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

    if (activeLayers.includes('manzanas_censales') && layerData.manzanas) {
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

    return result
  }, [activeLayers, layerData, selectedCategory])

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

      {popup && (
        <div
          style={{
            position: 'absolute',
            left: popup.x + 12,
            top: popup.y - 12,
            background: 'var(--bg-card)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: '10px 14px',
            fontSize: 12,
            color: 'var(--text-primary)',
            maxWidth: 280,
            boxShadow: '0 4px 16px rgba(0,0,0,0.18)',
            zIndex: 20,
            pointerEvents: 'auto',
          }}
        >
          <button
            onClick={() => setPopup(null)}
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
      )}
    </div>
  )
}

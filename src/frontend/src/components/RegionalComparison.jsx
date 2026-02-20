import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useStore } from '../store'
import { SkeletonChart } from './Skeleton'

const API = '/api'

export default function RegionalComparison() {
  const [homicidiosData, setHomicidiosData] = useState(null)
  const [icfesData, setIcfesData] = useState(null)
  const [desempleoData, setDesempleoData] = useState(null)
  const [ircaData, setIrcaData] = useState(null)
  const [empleoData, setEmpleoData] = useState(null)

  useEffect(() => {
    // Fetch real rankings from TerriData
    const fetchRanking = (indicador, setter, key) => {
      fetch(`${API}/analytics/ranking?indicador=${encodeURIComponent(indicador)}&order=desc`)
        .then(r => r.ok ? r.json() : [])
        .then(data => {
          if (Array.isArray(data) && data.length > 0) {
            setter(data.map(d => ({
              name: d.municipio?.replace('Apartadó', 'Apartadó')
                ?.replace('San Pedro De Urabá', 'S. Pedro')
                ?.replace('San Juan De Urabá', 'S. Juan')
                ?.replace('Vigía Del Fuerte', 'Vigía'),
              [key]: d.valor,
            })))
          }
        })
        .catch(() => {})
    }

    fetchRanking('Tasa de homicidios por cada 100.000 habitantes', setHomicidiosData, 'homicidios')
    fetchRanking('Puntaje promedio Pruebas Saber 11 - Matemáticas', setIcfesData, 'icfes')
    fetchRanking('Tasa de desempleo', setDesempleoData, 'desempleo')
    fetchRanking('Índice de riesgo de la calidad del agua -IRCA-', setIrcaData, 'irca')

    // Fetch employment concentration data
    fetch(`${API}/analytics/laboral/concentracion`)
      .then(r => r.ok ? r.json() : [])
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setEmpleoData(data.map(d => ({
            name: d.municipio?.replace('San Pedro De Urabá', 'S. Pedro')
              ?.replace('San Juan De Urabá', 'S. Juan')
              ?.replace('Vigía Del Fuerte', 'Vigía'),
            vacantes: d.ofertas,
          })))
        }
      })
      .catch(() => {})
  }, [])

  const chartStyle = { background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border)', padding: 16 }
  const tooltipStyle = { background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 8 }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h3 className="section-title">Comparativa Regional (Urabá)</h3>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 16 }}>
          Comparación de indicadores clave entre los municipios de la región de Urabá (TerriData - DNP).
        </p>
      </div>

      <div style={chartStyle}>
        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
          Vacantes Laborales por Municipio
        </h4>
        {empleoData ? (
          <div style={{ height: 250 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={empleoData} margin={{ bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={10} interval={0} angle={-45} textAnchor="end" />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="vacantes" fill="#FA8C16" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : <SkeletonChart />}
        <p style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8 }}>
          Fuente: Scraping multi-portal (ComputTrabajo, elempleo, Indeed, Comfama, LinkedIn)
        </p>
      </div>

      <div style={chartStyle}>
        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
          Tasa de Homicidios (por 100.000 hab.)
        </h4>
        {homicidiosData ? (
          <div style={{ height: 250 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={homicidiosData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
                <XAxis type="number" stroke="var(--text-muted)" fontSize={11} />
                <YAxis dataKey="name" type="category" stroke="var(--text-muted)" fontSize={11} width={70} />
                <Tooltip contentStyle={tooltipStyle} itemStyle={{ fontSize: 12 }} />
                <Bar dataKey="homicidios" fill="var(--semantic-negative)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : <SkeletonChart />}
      </div>

      <div style={chartStyle}>
        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
          Promedio ICFES Saber 11 - Matemáticas
        </h4>
        {icfesData ? (
          <div style={{ height: 250 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={icfesData} margin={{ bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={10} interval={0} angle={-45} textAnchor="end" />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="icfes" fill="var(--accent-primary)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : <SkeletonChart />}
      </div>

      <div style={chartStyle}>
        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
          Tasa de Desempleo (%)
        </h4>
        {desempleoData ? (
          <div style={{ height: 250 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={desempleoData} margin={{ bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={10} interval={0} angle={-45} textAnchor="end" />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="desempleo" fill="#ff7300" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : <SkeletonChart />}
      </div>

      <div style={chartStyle}>
        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
          Indice de Riesgo de Calidad de Agua (IRCA)
        </h4>
        {ircaData ? (
          <div style={{ height: 250 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ircaData} margin={{ bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={10} interval={0} angle={-45} textAnchor="end" />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="irca" fill="#00C49F" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : <SkeletonChart />}
        <p style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8 }}>
          Nota: Un IRCA más alto indica mayor riesgo (0-5: Sin Riesgo, 80-100: Riesgo Inviable Sanitariamente).
        </p>
      </div>
    </div>
  )
}

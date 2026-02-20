import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useStore } from '../store'

const MOCK_REGIONAL_DATA = [
  { name: 'Apartadó', homicidios: 42, desempleo: 12.5, icfes: 265, poblacion: 210000, irca: 2.5 },
  { name: 'Turbo', homicidios: 38, desempleo: 14.2, icfes: 242, poblacion: 185000, irca: 15.8 },
  { name: 'Carepa', homicidios: 15, desempleo: 11.8, icfes: 258, poblacion: 62000, irca: 3.2 },
  { name: 'Chigorodó', homicidios: 18, desempleo: 13.5, icfes: 251, poblacion: 85000, irca: 5.4 },
  { name: 'Necoclí', homicidios: 12, desempleo: 15.1, icfes: 238, poblacion: 45000, irca: 22.1 },
  { name: 'S. Pedro', homicidios: 8, desempleo: 12.9, icfes: 235, poblacion: 32000, irca: 18.5 },
  { name: 'S. Juan', homicidios: 5, desempleo: 13.2, icfes: 232, poblacion: 28000, irca: 12.3 },
  { name: 'Arboletes', homicidios: 7, desempleo: 14.5, icfes: 245, poblacion: 35000, irca: 8.9 },
  { name: 'Mutatá', homicidios: 4, desempleo: 16.2, icfes: 230, poblacion: 22000, irca: 4.1 },
  { name: 'Murindó', homicidios: 2, desempleo: 18.5, icfes: 215, poblacion: 5000, irca: 45.0 },
  { name: 'Vigía', homicidios: 3, desempleo: 17.8, icfes: 218, poblacion: 6000, irca: 48.2 },
]

export default function RegionalComparison() {
  const selectedMunicipio = useStore(s => s.selectedMunicipio)
  const [icfesRanking, setIcfesRanking] = useState([])

  useEffect(() => {
    fetch('/api/analytics/ranking?indicador=Puntaje+global+promedio+Saber+11')
      .then(r => r.json())
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setIcfesRanking(data.map(d => ({ name: d.municipio, icfes: d.valor })))
        }
      })
      .catch(e => console.error('Failed to fetch icfes ranking:', e))
  }, [])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h3 className="section-title">Comparativa Regional (Urabá)</h3>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 16 }}>
          Comparación de indicadores clave entre los municipios de la región de Urabá.
        </p>
      </div>

      <div style={{ background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border)', padding: 16 }}>
        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
          Homicidios por Municipio (2025)
        </h4>
        <div style={{ height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={MOCK_REGIONAL_DATA} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" horizontal={false} />
              <XAxis type="number" stroke="var(--text-muted)" fontSize={11} />
              <YAxis dataKey="name" type="category" stroke="var(--text-muted)" fontSize={11} width={70} />
              <Tooltip 
                contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 8 }}
                itemStyle={{ fontSize: 12 }}
              />
              <Bar dataKey="homicidios" fill="var(--semantic-negative)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border)', padding: 16 }}>
        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
          Promedio ICFES Saber 11
        </h4>
        <div style={{ height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={icfesRanking.length > 0 ? icfesRanking : MOCK_REGIONAL_DATA} margin={{ bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={10} interval={0} angle={-45} textAnchor="end" />
              <YAxis domain={[200, 300]} stroke="var(--text-muted)" fontSize={11} />
              <Tooltip 
                contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 8 }}
              />
              <Bar dataKey="icfes" fill="var(--accent-primary)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border)', padding: 16 }}>
        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
          Desempleo (%)
        </h4>
        <div style={{ height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={MOCK_REGIONAL_DATA} margin={{ bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={10} interval={0} angle={-45} textAnchor="end" />
              <YAxis stroke="var(--text-muted)" fontSize={11} />
              <Tooltip 
                contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 8 }}
              />
              <Bar dataKey="desempleo" fill="#ff7300" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ background: 'var(--bg-card)', borderRadius: 8, border: '1px solid var(--border)', padding: 16 }}>
        <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: 'var(--text-primary)' }}>
          Indice de Riesgo de Calidad de Agua (IRCA)
        </h4>
        <div style={{ height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={MOCK_REGIONAL_DATA} margin={{ bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={10} interval={0} angle={-45} textAnchor="end" />
              <YAxis stroke="var(--text-muted)" fontSize={11} />
              <Tooltip 
                contentStyle={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: 8 }}
              />
              <Bar dataKey="irca" fill="#00C49F" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 8 }}>
          Nota: Un IRCA más alto indica mayor riesgo (0-5: Sin Riesgo, 80-100: Riesgo Inviable Sanitariamente).
        </p>
      </div>
    </div>
  )
}

import os
import time
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import requests

load_dotenv()

def scrape_google_places_regional():
    db_url = os.getenv("DATABASE_URL")
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not db_url or not api_key:
        print("Error: DATABASE_URL o GOOGLE_MAPS_API_KEY no configurados")
        return
    
    engine = create_engine(db_url)
    
    # 1. Obtener los centroides de las veredas cargadas para usarlos como puntos de búsqueda
    print("Obteniendo centroides de veredas desde Supabase...")
    with engine.connect() as conn:
        query = """
            SELECT dane_code, 
                   ST_X(ST_Centroid(geom)) as lon, 
                   ST_Y(ST_Centroid(geom)) as lat
            FROM cartografia.veredas_mgn
        """
        df_veredas = pd.read_sql(text(query), conn)
    
    print(f"Total veredas a procesar: {len(df_veredas)}")
    
    # Categorías críticas para inteligencia territorial
    categories = [
        "hospital", "pharmacy", "school", "bank", "atm", 
        "supermarket", "grocery_or_supermarket", "gas_station",
        "police", "local_government_office"
    ]
    
    results = []
    processed_place_ids = set()
    
    # 2. Iniciar barrido radial (Nearby Search)
    # Nota: Para evitar costos excesivos, procesaremos una muestra representativa o usaremos radios más grandes
    # pero como el usuario pidió "TOTAL", haremos un barrido sistemático.
    
    count = 0
    for _, vereda in df_veredas.iterrows():
        count += 1
        if count % 10 == 0:
            print(f"Procesando vereda {count}/{len(df_veredas)}...")
            
        for cat in categories:
            url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={vereda.lat},{vereda.lon}&radius=5000&type={cat}&key={api_key}"
            
            try:
                response = requests.get(url).json()
                if response.get("status") == "OK":
                    for place in response.get("results", []):
                        pid = place.get("place_id")
                        if pid not in processed_place_ids:
                            processed_place_ids.add(pid)
                            results.append({
                                "place_id": pid,
                                "name": place.get("name"),
                                "category": cat,
                                "address": place.get("vicinity"),
                                "rating": place.get("rating"),
                                "user_ratings_total": place.get("user_ratings_total"),
                                "lat": place["geometry"]["location"]["lat"],
                                "lon": place["geometry"]["location"]["lng"],
                                "dane_code": vereda.dane_code
                            })
                elif response.get("status") == "OVER_QUERY_LIMIT":
                    print("⚠️ Límite de cuota de Google Maps alcanzado. Pausando...")
                    time.sleep(2)
            except Exception as e:
                print(f"Error en vereda {vereda.dane_code}: {e}")
        
        # Guardar lotes de 50 para no perder progreso y no saturar memoria
        if len(results) >= 50:
            save_places_to_db(results, engine)
            results = []
            
    # Guardar remanente
    if results:
        save_places_to_db(results, engine)
    
    print(f"Scraping completado. Total lugares únicos encontrados: {len(processed_place_ids)}")

def save_places_to_db(data, engine):
    # Limpieza de datos: convertir NaN a None para SQL
    df = pd.DataFrame(data).replace({pd.NA: None, float('nan'): None})
    
    with engine.begin() as conn:
        # Crear esquema si no existe
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS servicios;"))
        # Crear tabla si no existe
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS servicios.google_places_regional (
                place_id TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                address TEXT,
                rating FLOAT,
                user_ratings_total INTEGER,
                lat FLOAT,
                lon FLOAT,
                dane_code TEXT,
                geom geometry(Point, 4326),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # Insertar datos usando ON CONFLICT para actualizar
        for _, row in df.iterrows():
            # Asegurar que urt sea entero o None
            urt = int(row.user_ratings_total) if row.user_ratings_total is not None else None
            
            conn.execute(text("""
                INSERT INTO servicios.google_places_regional 
                (place_id, name, category, address, rating, user_ratings_total, lat, lon, dane_code, geom)
                VALUES (:pid, :name, :cat, :addr, :rat, :urt, :lat, :lon, :dane, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                ON CONFLICT (place_id) DO UPDATE SET
                    rating = EXCLUDED.rating,
                    user_ratings_total = EXCLUDED.user_ratings_total,
                    updated_at = CURRENT_TIMESTAMP;
            """), {
                "pid": row.place_id, "name": str(row.name), "cat": row.category, 
                "addr": row.address, "rat": row.rating, "urt": urt,
                "lat": row.lat, "lon": row.lon, "dane": row.dane_code
            })

if __name__ == "__main__":
    scrape_google_places_regional()

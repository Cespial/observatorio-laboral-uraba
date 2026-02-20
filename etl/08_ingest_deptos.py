import os
import geopandas as gpd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def ingest_departamentos():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found")
        return
    
    engine = create_engine(db_url)
    
    # Path to Departments
    depto_path = "/Users/cristianespinal/Downloads/Departamentos_Diciembre_2025_shp/Depto.shp"
    
    print(f"Leyendo Departamentos: {depto_path}")
    if not os.path.exists(depto_path):
        print("Error: Depto path not found")
        return

    gdf = gpd.read_file(depto_path)
    print(f"Total departamentos leídos: {len(gdf)}")
    
    # Antioquia es DPTO_CCDGO = '05'
    gdf = gdf.to_crs(epsg=4326)
    
    print("Subiendo a Supabase (cartografia.departamentos)...")
    
    # Fallback WKT manual for Supavisor compatibility
    import pandas as pd
    df = pd.DataFrame(gdf.drop(columns='geometry'))
    df['wkt_geom'] = gdf.geometry.apply(lambda x: x.wkt)

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS cartografia;"))
        conn.execute(text("DROP TABLE IF EXISTS cartografia.departamentos_temp;"))
    
    df.to_sql("departamentos_temp", engine, schema="cartografia", if_exists="replace", index=False)
    
    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE cartografia.departamentos_temp 
            ADD COLUMN geom geometry(MultiPolygon, 4326);
            
            UPDATE cartografia.departamentos_temp 
            SET geom = ST_Multi(ST_GeomFromText(wkt_geom, 4326));
            
            ALTER TABLE cartografia.departamentos_temp DROP COLUMN wkt_geom;
            
            DROP TABLE IF EXISTS cartografia.departamentos;
            ALTER TABLE cartografia.departamentos_temp RENAME TO departamentos;
        """))
    
    print("Ingesta de departamentos completa.")

if __name__ == "__main__":
    ingest_departamentos()

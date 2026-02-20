import os
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Municipios Urabá (Solo el código de municipio de 3 dígitos)
URABA_MPIO_CODES = [
    "045", "837", "172", "147", "490", 
    "051", "665", "659", "480", "475", "873"
]

def ingest_mgn_veredas():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found")
        return
    
    engine = create_engine(db_url)
    
    # Path to MGN
    mgn_path = "/Users/cristianespinal/Downloads/WGS84_MGN2019_00_COLOMBIA/MGN/MGN_RUR_SECCION.shp"
    
    print(f"Leyendo MGN Rural: {mgn_path}")
    if not os.path.exists(mgn_path):
        print("Error: MGN path not found")
        return

    gdf = gpd.read_file(mgn_path)
    print(f"Total registros leídos: {len(gdf)}")
    
    # Antioquia filter first
    gdf_ant = gdf[gdf['DPTO_CCDGO'].astype(str).str.zfill(2) == "05"].copy()
    print(f"Registros Antioquia: {len(gdf_ant)}")

    gdf_uraba = gdf_ant[gdf_ant['MPIO_CCDGO'].astype(str).str.zfill(3).isin(URABA_MPIO_CODES)].copy()
    print(f"Registros Urabá filtrados: {len(gdf_uraba)}")

    if len(gdf_uraba) == 0:
        print("No se encontraron datos para los códigos de Urabá en Antioquia")
        return

    # Prepare for PostGIS
    gdf_uraba = gdf_uraba.to_crs(epsg=4326)
    gdf_uraba['dane_code'] = "05" + gdf_uraba['MPIO_CCDGO'].astype(str).str.zfill(3)
    
    print("Subiendo a Supabase (via WKT DataFrame)...")
    
    # Create schema and extension
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS cartografia;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))

    # Convert GeoDataFrame to standard DataFrame with WKT geometry
    df = pd.DataFrame(gdf_uraba.drop(columns='geometry'))
    df['wkt_geom'] = gdf_uraba.geometry.apply(lambda x: x.wkt)

    # Use to_sql with the engine
    df.to_sql("veredas_mgn_temp", engine, schema="cartografia", if_exists="replace", index=False)
    
    # Convert WKT to actual geometry column
    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE cartografia.veredas_mgn_temp 
            ADD COLUMN geom geometry(Geometry, 4326);
            
            UPDATE cartografia.veredas_mgn_temp 
            SET geom = ST_GeomFromText(wkt_geom, 4326);
            
            ALTER TABLE cartografia.veredas_mgn_temp DROP COLUMN wkt_geom;
            
            DROP TABLE IF EXISTS cartografia.veredas_mgn;
            ALTER TABLE cartografia.veredas_mgn_temp RENAME TO veredas_mgn;
        """))
    
    print("Ingesta completa exitosa (via WKT manual).")

if __name__ == "__main__":
    ingest_mgn_veredas()

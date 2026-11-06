import geopandas as gpd

RUTA_ORIGINAL = "../datos/geometrias/Municipios.geojson"
RUTA_SALIDA = "../datos/geometrias/municipios_simplificado.geojson"

print("Cargando el GeoJSON original (puede tardar un poco)...")
gdf = gpd.read_file(RUTA_ORIGINAL)

print(f"Municipios cargados: {len(gdf)}")
print(f"Sistema de coordenadas original: {gdf.crs}")

# Convertir a WGS84 (el que usa Leaflet)
gdf = gdf.to_crs(epsg=4326)

# Simplificar: tolerance=0.005 grados ≈ 500 m de precisión.
# Para un mapa de España a nivel municipal es más que suficiente.
print("Simplificando geometrías...")
gdf["geometry"] = gdf["geometry"].simplify(tolerance=0.001, preserve_topology=True)

# Guardar
gdf.to_file(RUTA_SALIDA, driver="GeoJSON")
print(f"Archivo guardado en: {RUTA_SALIDA}")
import pandas as pd
import geopandas as gpd
import json
from pathlib import Path

# 1. Resolver las rutas
RAIZ = Path(__file__).resolve().parent.parent
RUTA_RESULTADOS = RAIZ / "datos" / "resultados_historicos.csv"
RUTA_GEOMETRIAS = RAIZ / "datos" / "geometrias" / "municipios_simplificado.geojson"
RUTA_SALIDA_GEOJSON = RAIZ / "web" / "mapa.geojson"
RUTA_SALIDA_JSON = RAIZ / "web" / "resultados.json"

# 2. Cargar los resultados electorales (CSV)
print("Cargando resultados...")
resultados = pd.read_csv(RUTA_RESULTADOS)
# Asegurarnos de que el código de municipio sea texto de 5 dígitos
resultados["codigo_municipio"] = resultados["codigo_municipio"].astype(str).str.zfill(5)

# 3. Calcular el partido ganador por municipio
# Agrupamos por municipio y partido, sumamos votos, y nos quedamos con el máximo
ganadores = resultados.loc[resultados.groupby("codigo_municipio")["votos"].idxmax()]
ganadores = ganadores[["codigo_municipio", "partido", "votos"]]
ganadores.columns = ["codigo_municipio", "partido_ganador", "votos_ganador"]

# 4. Cargar las geometrías (Shapefile)
print("Cargando geometrías...")
geometrias = gpd.read_file(RUTA_GEOMETRIAS)

# 5. Asegurarnos de que la columna de código INE se llama igual en ambos
# (En los Shapefiles del INE suele llamarse "COD_INE" o "codigo_municipio")
# Ajusta el nombre según tu archivo. Aquí asumimos que se llama "COD_INE".
geometrias["codigo_municipio"] = geometrias["CUMUN"].astype(str).str.zfill(5)

# 6. Unir (join) geometrías con ganadores
mapa = geometrias.merge(ganadores, on="codigo_municipio", how="left")

# 7. Convertir a EPSG:4326 (el sistema de coordenadas que usa Leaflet)
mapa = mapa.to_crs(epsg=4326)

# 8. Guardar como GeoJSON
print("Guardando GeoJSON...")
mapa.to_file(RUTA_SALIDA_GEOJSON, driver="GeoJSON")

# 9. Guardar un JSON con los datos de ganadores (para los popups)
print("Guardando JSON de resultados...")
mapa[["codigo_municipio", "partido_ganador", "votos_ganador"]].to_json(
    RUTA_SALIDA_JSON, orient="records", force_ascii=False
)

print("¡Proceso completado!")

import pandas as pd
import geopandas as gpd
import json

# 1. Cargar los resultados electorales (CSV)
print("Cargando resultados...")
resultados = pd.read_csv("../datos/resultados_historicos.csv")
# Asegurarnos de que el código de municipio sea texto de 5 dígitos
resultados["codigo_municipio"] = resultados["codigo_municipio"].astype(str).str.zfill(5)

# 2. Calcular el partido ganador por municipio
# Agrupamos por municipio y partido, sumamos votos, y nos quedamos con el máximo
ganadores = resultados.loc[resultados.groupby("codigo_municipio")["votos"].idxmax()]
ganadores = ganadores[["codigo_municipio", "partido", "votos"]]
ganadores.columns = ["codigo_municipio", "partido_ganador", "votos_ganador"]

# 3. Cargar las geometrías (Shapefile)
print("Cargando geometrías...")
geometrias = gpd.read_file("../datos/geometrias/Municipios.geojson")

# 4. Asegurarnos de que la columna de código INE se llama igual en ambos
# (En los Shapefiles del INE suele llamarse "COD_INE" o "codigo_municipio")
# Ajusta el nombre según tu archivo. Aquí asumimos que se llama "COD_INE".
geometrias["codigo_municipio"] = geometrias["CUMUN"].astype(str).str.zfill(5)

# 5. Unir (join) geometrías con ganadores
mapa = geometrias.merge(ganadores, on="codigo_municipio", how="left")

# 6. Convertir a EPSG:4326 (el sistema de coordenadas que usa Leaflet)
mapa = mapa.to_crs(epsg=4326)

# 7. Simplificar la geometría para que el archivo pese menos (opcional pero recomendado)
mapa["geometry"] = mapa["geometry"].simplify(tolerance=0.001, preserve_topology=True)

# 8. Guardar como GeoJSON
print("Guardando GeoJSON...")
mapa.to_file("E:/proyecto_elecciones/web/mapa.geojson", driver="GeoJSON")

# 9. Guardar un JSON con los datos de ganadores (para los popups)
print("Guardando JSON de resultados...")
mapa[["codigo_municipio", "partido_ganador", "votos_ganador"]].to_json(
    "../web/resultados.json", orient="records", force_ascii=False
)

print("¡Proceso completado!")
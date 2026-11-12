import pandas as pd
import geopandas as gpd
import json
from pathlib import Path

# Resolver las rutas
RAIZ = Path(__file__).resolve().parent.parent
RUTA_RESULTADOS = RAIZ / "datos" / "resultados_historicos.csv"
RUTA_GEOMETRIAS = RAIZ / "datos" / "geometrias" / "municipios_simplificado.geojson"
RUTA_SALIDA_GEOJSON = RAIZ / "web" / "mapa.geojson"
RUTA_SALIDA_JSON = RAIZ / "web" / "resultados.json"

# Partidos que SIEMPRE queremos rastrear, aunque no ganen en ningún municipio
PARTIDOS_PREDEFINIDOS = {'PSOE', 'PP', 'VOX', 'SUMAR', 'ERC', 'JUNTS', 'EH_BILDU', 'PNV', 'BNG'}

def normalizar_partido(nombre):
    """Mapea variantes de nombres a una etiqueta estándar."""
    p = str(nombre).upper()
    if 'PSOE' in p or 'PSC' in p or 'PSDEG' in p: return 'PSOE'
    if p == 'PP' or 'PARTIDO POPULAR' in p:      return 'PP'
    if 'VOX' in p:                                return 'VOX'
    if 'SUMAR' in p or 'PODEMOS' in p:            return 'SUMAR'
    if 'ERC' in p or 'ESQUERRA REPUBLICANA' in p: return 'ERC'
    if 'JUNTS' in p:                              return 'JUNTS'
    if 'BILDU' in p:                              return 'EH_BILDU'
    if 'PNV' in p or 'EAJ' in p:                  return 'PNV'
    if 'BNG' in p or 'BLOQUE NACIONALISTA' in p:  return 'BNG'
    # Para el resto, mantenemos el nombre original en mayúsculas
    return p.strip()

# Cargar los resultados electorales (CSV)
print("Cargando resultados...")
resultados = pd.read_csv(RUTA_RESULTADOS)
resultados["codigo_municipio"] = resultados["codigo_municipio"].astype(str).str.zfill(5)
resultados["partido_norm"] = resultados["partido"].apply(normalizar_partido)

# --- 1ª agregación: una fila por municipio y partido normalizado ---
agrup = resultados.groupby(["codigo_municipio", "partido_norm"], as_index=False)["votos"].sum()

# --- Identificar partidos que ganan en al menos un municipio ---
idx_ganadores_preliminar = agrup.groupby("codigo_municipio")["votos"].idxmax()
partidos_ganadores = set(agrup.loc[idx_ganadores_preliminar, "partido_norm"].unique())
print(f"Partidos que ganan en algún municipio: {sorted(partidos_ganadores)}")

# --- Partidos que vamos a rastrear ---
partidos_seguimiento = PARTIDOS_PREDEFINIDOS | partidos_ganadores

# --- Reclasificar: lo que no esté en seguimiento pasa a OTROS ---
agrup["partido_final"] = agrup["partido_norm"].apply(
    lambda p: p if p in partidos_seguimiento else 'OTROS'
)

# --- 2ª agregación: por si varios partidos han colapsado en OTROS ---
agrup = agrup.groupby(["codigo_municipio", "partido_final"], as_index=False)["votos"].sum()

# --- Ganador definitivo por municipio (después de la reclasificación) ---
idx_ganadores = agrup.groupby("codigo_municipio")["votos"].idxmax()
ganadores = agrup.loc[idx_ganadores].copy()
ganadores.columns = ["codigo_municipio", "partido_ganador", "votos_ganador"]

# --- Pivot: una fila por municipio, una columna votos_<PARTIDO> por partido ---
pivot = agrup.pivot(index="codigo_municipio", columns="partido_final", values="votos")
pivot = pivot.fillna(0).astype(int)
pivot.columns = [f"votos_{c}" for c in pivot.columns]
pivot = pivot.reset_index()

# --- Unir ganadores con el pivot ---
resultados_final = pivot.merge(ganadores, on="codigo_municipio", how="left")

print(f"Columnas de votos generadas: {[c for c in resultados_final.columns if c.startswith('votos_')]}")


# Cargar las geometrías (Shapefile)
print("Cargando geometrías...")
geometrias = gpd.read_file(RUTA_GEOMETRIAS)

# Asegurarnos de que la columna de código INE se llama igual en ambos

geometrias["codigo_municipio"] = geometrias["CUMUN"].astype(str).str.zfill(5)

# Unir (join) geometrías con ganadores
mapa = geometrias.merge(resultados_final, on="codigo_municipio", how="left")
mapa = mapa.to_crs(epsg=4326)

# Guardar como GeoJSON
print("Guardando GeoJSON...")
mapa.to_file(RUTA_SALIDA_GEOJSON, driver="GeoJSON")

# Guardar un JSON con los datos de ganadores (para los popups)
print("Guardando JSON de resultados...")
columnas_json = ["codigo_municipio", "partido_ganador", "votos_ganador"] + \
                [c for c in mapa.columns if c.startswith("votos_") and c != "votos_ganador"]
mapa[columnas_json].to_json(RUTA_SALIDA_JSON, orient="records", force_ascii=False)

print("¡Proceso completado!")

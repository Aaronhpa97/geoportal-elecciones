import csv
from collections import defaultdict   

# ------------------------------------------------------------
# 1. Leer el fichero de candidaturas (03*.DAT)
# ------------------------------------------------------------
def leer_candidaturas(ruta_fichero):
    partidos = {}
    with open(ruta_fichero, 'r', encoding='iso-8859-1') as f:
        for linea in f:
            codigo = linea[8:14].strip()
            nombre = linea[64:214].strip()
            if codigo:
                partidos[codigo] = nombre
    return partidos

# ------------------------------------------------------------
# 2. Leer resultados y AGREGAR votos por municipio + partido
# ------------------------------------------------------------
def convertir_resultados_a_csv(ruta_resultados, ruta_candidaturas, ruta_salida_csv):
    partidos = leer_candidaturas(ruta_candidaturas)

    # NUEVO: acumulador {(codigo_municipio, nombre_partido): votos_totales}
    acumulador = defaultdict(int)

    with open(ruta_resultados, 'r', encoding='iso-8859-1') as fin:
        for linea in fin:
            provincia = linea[11:13]
            municipio = linea[13:16]
            codigo_municipio = provincia + municipio  # ej. "28" + "079" = "28079"

            codigo_partido = linea[23:29].strip()
            votos_str = linea[29:36].strip()

            try:
                votos = int(votos_str)
            except ValueError:
                continue  # línea sin votos válidos (cabeceras, totales, etc.)

            nombre_partido = partidos.get(codigo_partido, codigo_partido)

            # NUEVO: sumar al acumulador en lugar de escribir directamente
            acumulador[(codigo_municipio, nombre_partido)] += votos

    # NUEVO: escribir el CSV una vez terminada la lectura, ya agregado
    with open(ruta_salida_csv, 'w', newline='', encoding='utf-8') as fout:
        writer = csv.writer(fout)
        writer.writerow(['codigo_municipio', 'partido', 'votos'])

        # Ordenamos por municipio y luego por votos descendentes (más legible)
        filas = sorted(
            acumulador.items(),
            key=lambda x: (x[0][0], -x[1])
        )
        for (codigo_municipio, nombre_partido), votos_totales in filas:
            writer.writerow([codigo_municipio, nombre_partido, votos_totales])

    print(f"CSV generado: {ruta_salida_csv}")
    print(f"Municipios únicos: {len({k[0] for k in acumulador})}")
    print(f"Filas (municipio × partido): {len(acumulador)}")

# ------------------------------------------------------------
# 3. Bloque principal
# ------------------------------------------------------------
if __name__ == '__main__':
    RUTA_CANDIDATURAS = 'F:/Users/Aaron/Downloads/GIS-Study/Geoportal Electoral/02202307_MESA/03022307.DAT'   # fichero de partidos
    RUTA_RESULTADOS   = 'F:/Users/Aaron/Downloads/GIS-Study/Geoportal Electoral/02202307_MESA/10022307.DAT'   # fichero de resultados 
    RUTA_SALIDA_CSV   = 'E:/proyecto_elecciones/datos/resultados_historicos.csv'

    convertir_resultados_a_csv(RUTA_RESULTADOS, RUTA_CANDIDATURAS, RUTA_SALIDA_CSV)
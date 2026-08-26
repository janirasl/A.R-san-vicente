"""
Limpieza conjunta de TODO el alquiler residencial: Idealista + Fotocasa,
combinando TODAS las sesiones de extraccion que haya en la carpeta del
proyecto (no solo dos fechas fijas) -- San Vicente del Raspeig.

Por que se limpian juntos:
Es el mismo mercado (alquiler de vivienda completa) y es habitual que la misma
vivienda este publicada en varios portales a la vez, o que la misma extraccion
se repita en fechas distintas -> hay que detectar y quitar esos duplicados
antes de usar los datos, si no, esa vivienda pesaria varias veces en las
medias/comparativas.

Descubrimiento automatico de fuentes (para que no haya que tocar este script
cada vez que se hace una nueva extraccion, p.ej. la quincenal programada):
  - Idealista: cualquier fichero que empiece por "idealista_san_vicente_raw"
    (idealista_san_vicente_raw.csv, idealista_san_vicente_raw_2026-08-24.csv,
    idealista_san_vicente_raw_2026-09-07.csv, ...).
  - Fotocasa: igual con "fotocasa_san_vicente_raw", EXCEPTO
    fotocasa_san_vicente_raw_con_grupo.csv (es la misma muestra que la version
    2026-08-24 con 2 columnas calculadas de mas -> se excluye para no duplicar).

Cada fichero puede venir en uno de dos esquemas (se detecta automaticamente
por las columnas de la cabecera, no por el nombre):
  - "original": precio;detalles;tag  (idealista)  /  precio;zona;habitaciones;
    banos;m2;detalle;tipo_alquiler  (fotocasa) -- sin columna fecha_captura,
    se usa la fecha del nombre del fichero si la tiene, si no 2026-08-26.
  - "fechado": fecha_captura,fuente,pagina,titulo,precio_mes_eur,habitaciones,
    superficie_m2,zona,planta,ascensor,descripcion_resumida,url_fuente
    (idealista) / fecha_captura,fuente,titulo_o_referencia,zona,
    precio_publicado_eur_mes,habitaciones,superficie_m2,planta,banos,
    tipo_alquiler,descripcion_resumida,ascensor (fotocasa) -- este es el
    formato que debe usar cualquier extraccion nueva (incluida la tarea
    programada quincenal), con el nombre idealista_san_vicente_raw_AAAA-MM-DD.csv
    / fotocasa_san_vicente_raw_AAAA-MM-DD.csv.

muestra_alquiler_estudiantes.csv NO se incluye: es un resumen manual de 10
anuncios sin campos suficientes para cruzarlos de forma fiable con el resto.

Salida: alquiler_residencial_limpio.csv con esquema unificado:
    fuente, fecha_captura, precio_mes, habitaciones, m2, zona, planta,
    ascensor, banos, garaje, tipo_alquiler, texto_original

es_duplicado_cruzado = True en las filas que se han identificado como el mismo
anuncio repetido (en otro portal y/o en otra fecha de captura). Se conserva
solo la primera aparicion (por orden de fecha_captura, la mas antigua); las
demas se marcan y se quitan en la version final -- asi, cuando el mismo piso
sigue publicado semana tras semana, solo cuenta una vez y no infla la muestra.
"""

import os
import re
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent
OUT_DIR = SCRIPT_DIR.parent / "limpio"


def parse_precio(txt):
    """'925€/mes', '1150', '1.200' -> 925.0 / 1150.0 / 1200.0 (float, euros/mes)."""
    if pd.isna(txt) or txt == "":
        return None
    txt = str(txt).replace("€/mes", "").replace("€", "").strip()
    txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        return None


def parse_habitaciones_texto(detalles):
    m = re.search(r"(\d+)\s*hab", str(detalles))
    return int(m.group(1)) if m else None


def parse_m2_texto(detalles):
    m = re.search(r"([\d.,]+)\s*m²", str(detalles))
    if not m:
        return None
    val = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(val)
    except ValueError:
        return None


def parse_planta_texto(detalles):
    m = re.search(r"(Bajo|Entreplanta|\d+ª)\s*planta", str(detalles), re.IGNORECASE)
    return m.group(0) if m else None


def parse_ascensor_texto(detalles):
    d = str(detalles).lower()
    if "con ascensor" in d or d.strip() in ("sí", "si"):
        return True
    if "sin ascensor" in d or d.strip() == "no":
        return False
    return None


def parse_garaje_texto(detalles):
    return "garaje" in str(detalles).lower()


def extraer_fecha_de_nombre(path):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", path.name)
    return m.group(1) if m else None


def leer_cabecera(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.readline()


# ---------------------------------------------------------------------------
# Descubrimiento de ficheros
# ---------------------------------------------------------------------------
def descubrir_archivos_idealista():
    return sorted(RAW_DIR.glob("idealista_san_vicente_raw*.csv"))


def descubrir_archivos_fotocasa():
    return sorted(p for p in RAW_DIR.glob("fotocasa_san_vicente_raw*.csv") if "con_grupo" not in p.name)


# ---------------------------------------------------------------------------
# Carga por esquema (auto-detectado por columnas de cabecera)
# ---------------------------------------------------------------------------
def cargar_idealista(path):
    cabecera = leer_cabecera(path)
    fecha_nombre = extraer_fecha_de_nombre(path)

    if "precio_mes_eur" in cabecera:
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
        df = df.dropna(subset=["precio_mes_eur"])
        out = pd.DataFrame(index=df.index)
        out["fuente"] = "idealista"
        out["fecha_captura"] = df["fecha_captura"] if "fecha_captura" in df.columns else (fecha_nombre or "desconocida")
        out["precio_mes"] = df["precio_mes_eur"].apply(parse_precio)
        out["habitaciones"] = pd.to_numeric(df["habitaciones"], errors="coerce")
        out["m2"] = pd.to_numeric(df["superficie_m2"], errors="coerce")
        out["zona"] = df["zona"]
        out["planta"] = df["planta"]
        out["ascensor"] = df["ascensor"].apply(parse_ascensor_texto)
        out["banos"] = None
        out["garaje"] = df["descripcion_resumida"].apply(parse_garaje_texto)
        out["tipo_alquiler"] = df["descripcion_resumida"].apply(
            lambda t: "temporada" if isinstance(t, str) and "temporada" in t.lower() else "anual/no_especificado"
        )
        out["texto_original"] = (
            df["titulo"].astype(str) + " | " + df["precio_mes_eur"].astype(str)
            + " | " + df["descripcion_resumida"].astype(str)
        )
    else:
        # esquema "original": precio;detalles;tag
        df = pd.read_csv(path, sep=";", dtype=str)
        df = df.dropna(subset=["precio"])
        out = pd.DataFrame(index=df.index)
        out["fuente"] = "idealista"
        out["fecha_captura"] = fecha_nombre or "2026-08-26"  # fichero original, sin fecha en el nombre
        out["precio_mes"] = df["precio"].apply(parse_precio)
        out["habitaciones"] = df["detalles"].apply(parse_habitaciones_texto)
        out["m2"] = df["detalles"].apply(parse_m2_texto)
        out["zona"] = None
        out["planta"] = df["detalles"].apply(parse_planta_texto)
        out["ascensor"] = df["detalles"].apply(parse_ascensor_texto)
        out["banos"] = None
        out["garaje"] = df["detalles"].apply(parse_garaje_texto)
        out["tipo_alquiler"] = df["tag"].apply(
            lambda t: "temporada" if isinstance(t, str) and "temporada" in t.lower() else "anual/no_especificado"
        )
        out["texto_original"] = df["precio"].astype(str) + " | " + df["detalles"].astype(str)

    return out


def cargar_fotocasa(path):
    cabecera = leer_cabecera(path)
    fecha_nombre = extraer_fecha_de_nombre(path)

    if "precio_publicado_eur_mes" in cabecera:
        df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
        df = df.dropna(subset=["precio_publicado_eur_mes"])
        out = pd.DataFrame(index=df.index)
        out["fuente"] = "fotocasa"
        out["fecha_captura"] = df["fecha_captura"] if "fecha_captura" in df.columns else (fecha_nombre or "desconocida")
        out["precio_mes"] = df["precio_publicado_eur_mes"].apply(parse_precio)
        out["habitaciones"] = pd.to_numeric(df["habitaciones"], errors="coerce")
        out["m2"] = pd.to_numeric(df["superficie_m2"], errors="coerce")
        out["zona"] = df["zona"]
        out["planta"] = df["planta"]
        out["ascensor"] = df["ascensor"].apply(parse_ascensor_texto)
        out["banos"] = pd.to_numeric(df["banos"], errors="coerce")
        out["garaje"] = df["descripcion_resumida"].apply(parse_garaje_texto)
        out["tipo_alquiler"] = df["tipo_alquiler"].apply(
            lambda t: "temporada" if isinstance(t, str) and "temporada" in t.lower() else "anual/no_especificado"
        )
        out["texto_original"] = (
            df["titulo_o_referencia"].astype(str) + " | " + df["precio_publicado_eur_mes"].astype(str)
            + " | " + df["descripcion_resumida"].astype(str)
        )
    else:
        # esquema "original": precio;zona;habitaciones;banos;m2;detalle;tipo_alquiler
        df = pd.read_csv(path, sep=";", dtype=str)
        df = df.dropna(subset=["precio"])
        out = pd.DataFrame(index=df.index)
        out["fuente"] = "fotocasa"
        out["fecha_captura"] = fecha_nombre or "2026-08-26"
        out["precio_mes"] = df["precio"].apply(parse_precio)
        out["habitaciones"] = pd.to_numeric(df["habitaciones"], errors="coerce")
        out["m2"] = pd.to_numeric(df["m2"], errors="coerce")
        out["zona"] = df["zona"]
        out["planta"] = df["detalle"].apply(parse_planta_texto)
        out["ascensor"] = df["detalle"].apply(
            lambda d: True if "ascensor" in str(d).lower() and "sin ascensor" not in str(d).lower() else None
        )
        out["banos"] = None
        out["garaje"] = False
        out["tipo_alquiler"] = df["tipo_alquiler"].apply(
            lambda t: "temporada" if isinstance(t, str) and t.strip() != "" else "anual/no_especificado"
        )
        out["texto_original"] = df["precio"].astype(str) + " | " + df["zona"].astype(str) + " | " + df["detalle"].astype(str)

    return out


def marcar_duplicados(df):
    """
    Duplicado = mismo precio_mes, misma habitaciones y m2 muy similar (+-2 m2),
    sin importar de que portal o fecha venga -> con N extracciones acumuladas
    (2 portales x cuantas fechas haya), el mismo anuncio puede repetirse tanto
    entre portales como entre varias fechas de captura (sigue publicado semanas
    despues). Se ordena por fecha_captura antes de agrupar para quedarnos
    siempre con la aparicion MAS ANTIGUA de cada grupo (asi fecha_captura del
    registro que sobrevive refleja cuando se vio ese piso por primera vez).
    """
    df = df.copy()
    df = df.sort_values("fecha_captura", na_position="last").reset_index(drop=True)
    df["es_duplicado_cruzado"] = False
    df["m2_bin"] = (df["m2"] / 2).round() * 2

    con_datos = df.dropna(subset=["precio_mes", "habitaciones", "m2_bin"])
    grupos = con_datos.groupby(["precio_mes", "habitaciones", "m2_bin"])
    for _, idx in grupos.groups.items():
        if len(idx) > 1:
            resto = df.loc[idx].index[1:]
            df.loc[resto, "es_duplicado_cruzado"] = True

    return df.drop(columns=["m2_bin"])


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    archivos_idealista = descubrir_archivos_idealista()
    archivos_fotocasa = descubrir_archivos_fotocasa()
    print(f"Ficheros Idealista encontrados ({len(archivos_idealista)}): {[p.name for p in archivos_idealista]}")
    print(f"Ficheros Fotocasa encontrados ({len(archivos_fotocasa)}): {[p.name for p in archivos_fotocasa]}")
    print()

    fuentes = {}
    for p in archivos_idealista:
        fuentes[f"idealista::{p.name}"] = cargar_idealista(p)
    for p in archivos_fotocasa:
        fuentes[f"fotocasa::{p.name}"] = cargar_fotocasa(p)

    for nombre, df in fuentes.items():
        print(f"{nombre}: {len(df)} filas")

    combinado = pd.concat([df for df in fuentes.values() if not df.empty], ignore_index=True)
    combinado = marcar_duplicados(combinado)

    con_marcas_path = f"{OUT_DIR}/alquiler_residencial_con_marcas.csv"
    combinado.to_csv(con_marcas_path, sep=";", index=False)

    final = combinado[~combinado["es_duplicado_cruzado"]].drop(columns=["es_duplicado_cruzado"])
    out_path = f"{OUT_DIR}/alquiler_residencial_limpio.csv"
    final.to_csv(out_path, sep=";", index=False)

    n_total = len(combinado)
    n_dupes = combinado["es_duplicado_cruzado"].sum()
    print(f"\nTotal combinado ({len(fuentes)} ficheros): {n_total} | Duplicados detectados: {n_dupes}")
    print(f"Filas unicas tras deduplicar: {len(final)}")
    print(f"Version completa (con marca de duplicado, para auditar): {con_marcas_path}")
    print(f"Version final (UN SOLO CSV, sin duplicados) -> usar esta para el EDA: {out_path}")

    incompletos = combinado[combinado["precio_mes"].isna() | combinado["m2"].isna()]
    print(f"Filas con precio o m2 sin extraer (revisar manualmente): {len(incompletos)}")

    print("\n--- Comparativa rapida por fuente (antes de deduplicar) ---")
    print(combinado.groupby("fuente")["precio_mes"].agg(["count", "mean", "min", "max"]).round(0))
    print("\n--- Comparativa rapida por fecha de captura (antes de deduplicar) ---")
    print(combinado.groupby("fecha_captura")["precio_mes"].agg(["count", "mean", "min", "max"]).round(0))


if __name__ == "__main__":
    main()

"""
Limpieza conjunta de TODO el alquiler residencial: Idealista + Fotocasa,
combinando las dos sesiones de extraccion que hay (24 y 26 de agosto de 2026),
San Vicente del Raspeig.

Por que se limpian juntos:
Es el mismo mercado (alquiler de vivienda completa) y es habitual que la misma
vivienda este publicada en varios portales a la vez, o que la misma extraccion
se repita en fechas distintas -> hay que detectar y quitar esos duplicados
antes de usar los datos, si no, esa vivienda pesaria varias veces en las
medias/comparativas.

Fuentes que se combinan (4 en total):
  - idealista_san_vicente_raw.csv                  (26/08/2026)
  - idealista_san_vicente_raw_2026-08-24.csv        (24/08/2026)
  - fotocasa_san_vicente_raw.csv                    (26/08/2026)
  - fotocasa_san_vicente_raw_2026-08-24.csv         (24/08/2026)

(fotocasa_san_vicente_raw_con_grupo.csv NO se incluye aparte: es la misma
muestra que fotocasa_san_vicente_raw_2026-08-24.csv con dos columnas
calculadas de mas -> incluirla tambien duplicaria esas 47 filas.
muestra_alquiler_estudiantes.csv tampoco se incluye: es un resumen manual de
10 anuncios sin campos suficientes para cruzarlos de forma fiable con el resto;
se puede revisar aparte si hace falta.)

Salida: alquiler_residencial_limpio.csv con esquema unificado:
    fuente, fecha_captura, precio_mes, habitaciones, m2, zona, planta,
    ascensor, banos, garaje, tipo_alquiler, texto_original

es_duplicado_cruzado = True en las filas que se han identificado como el mismo
anuncio repetido (en otro portal y/o en la otra fecha de captura). Se conserva
solo la primera aparicion; las demas se marcan y se quitan en la version final.
"""

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


# ---------------------------------------------------------------------------
# Idealista, sesion del 26/08 (precio;detalles;tag)
# ---------------------------------------------------------------------------
def load_idealista_0826():
    df = pd.read_csv(f"{RAW_DIR}/idealista_san_vicente_raw.csv", sep=";", dtype=str)
    df = df.dropna(subset=["precio"])
    out = pd.DataFrame(index=df.index)
    out["fuente"] = "idealista"
    out["fecha_captura"] = "2026-08-26"
    out["precio_mes"] = df["precio"].apply(parse_precio)
    out["habitaciones"] = df["detalles"].apply(parse_habitaciones_texto)
    out["m2"] = df["detalles"].apply(parse_m2_texto)
    out["zona"] = None  # esta extraccion no capturo zona/barrio
    out["planta"] = df["detalles"].apply(parse_planta_texto)
    out["ascensor"] = df["detalles"].apply(parse_ascensor_texto)
    out["banos"] = None
    out["garaje"] = df["detalles"].apply(parse_garaje_texto)
    out["tipo_alquiler"] = df["tag"].apply(
        lambda t: "temporada" if isinstance(t, str) and "temporada" in t.lower() else "anual/no_especificado"
    )
    out["texto_original"] = df["precio"].astype(str) + " | " + df["detalles"].astype(str)
    return out


# ---------------------------------------------------------------------------
# Idealista, sesion del 24/08 (fecha_captura,fuente,pagina,titulo,precio_mes_eur,
# habitaciones,superficie_m2,zona,planta,ascensor,descripcion_resumida,url_fuente)
# ---------------------------------------------------------------------------
def load_idealista_0824():
    path = RAW_DIR / "idealista_san_vicente_raw_2026-08-24.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    df = df.dropna(subset=["precio_mes_eur"])
    out = pd.DataFrame(index=df.index)
    out["fuente"] = "idealista"
    out["fecha_captura"] = df["fecha_captura"]
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
    return out


# ---------------------------------------------------------------------------
# Fotocasa, sesion del 26/08 (precio;zona;habitaciones;banos;m2;detalle;tipo_alquiler)
# ---------------------------------------------------------------------------
def load_fotocasa_0826():
    df = pd.read_csv(f"{RAW_DIR}/fotocasa_san_vicente_raw.csv", sep=";", dtype=str)
    df = df.dropna(subset=["precio"])
    out = pd.DataFrame(index=df.index)
    out["fuente"] = "fotocasa"
    out["fecha_captura"] = "2026-08-26"
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


# ---------------------------------------------------------------------------
# Fotocasa, sesion del 24/08 (fecha_captura,fuente,titulo_o_referencia,zona,
# precio_publicado_eur_mes,habitaciones,superficie_m2,planta,banos,tipo_alquiler,
# descripcion_resumida,ascensor)
# ---------------------------------------------------------------------------
def load_fotocasa_0824():
    path = RAW_DIR / "fotocasa_san_vicente_raw_2026-08-24.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    df = df.dropna(subset=["precio_publicado_eur_mes"])
    out = pd.DataFrame(index=df.index)
    out["fuente"] = "fotocasa"
    out["fecha_captura"] = df["fecha_captura"]
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
    return out


def marcar_duplicados(df):
    """
    Duplicado = mismo precio_mes, misma habitaciones y m2 muy similar (+-2 m2),
    sin importar si viene del mismo portal/fecha o no -> ahora que combinamos
    4 extracciones (2 portales x 2 fechas), el mismo anuncio puede repetirse
    tanto entre portales como entre las dos sesiones de captura.
    Se conserva la primera fila de cada grupo duplicado y se marca el resto.
    """
    df = df.copy()
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
    import os
    os.makedirs(OUT_DIR, exist_ok=True)

    fuentes = {
        "idealista_2026-08-26": load_idealista_0826(),
        "idealista_2026-08-24": load_idealista_0824(),
        "fotocasa_2026-08-26": load_fotocasa_0826(),
        "fotocasa_2026-08-24": load_fotocasa_0824(),
    }

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
    print(f"\nTotal combinado (4 fuentes): {n_total} | Duplicados detectados: {n_dupes}")
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

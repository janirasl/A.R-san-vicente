"""
Limpieza conjunta de Idealista + Fotocasa (alquiler residencial), San Vicente del Raspeig.

Por qué se limpian juntos:
Son el mismo mercado (alquiler de vivienda completa) y es habitual que la misma
vivienda esté publicada en ambos portales a la vez -> hay que detectar y quitar
esos duplicados cruzados antes de usar los datos en el analisis, si no, esa
vivienda pesaria el doble en las medias/comparativas.

Salida: alquiler_residencial_limpio.csv con esquema unificado:
    fuente, precio_mes, habitaciones, m2, zona, planta, ascensor, garaje,
    tipo_alquiler, es_duplicado_cruzado, texto_original

es_duplicado_cruzado = True en las filas que se han identificado como el mismo
anuncio repetido en el otro portal (se conserva solo la primera aparicion,
las demas se marcan y se pueden filtrar).
"""

import re
from pathlib import Path

import pandas as pd

# Rutas relativas a la ubicacion del propio script (funciona en cualquier
# ordenador/sistema operativo mientras la carpeta "scripts" este dentro de la
# carpeta del proyecto, junto a los CSV en bruto).
SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent
OUT_DIR = SCRIPT_DIR.parent / "limpio"


def parse_precio(txt):
    """'925€/mes' o '1150' -> 925.0 (float, euros/mes)"""
    if pd.isna(txt) or txt == "":
        return None
    txt = str(txt).replace("€/mes", "").replace("€", "").strip()
    txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        return None


def parse_habitaciones_idealista(detalles):
    m = re.search(r"(\d+)\s*hab", str(detalles))
    return int(m.group(1)) if m else None


def parse_m2_idealista(detalles):
    m = re.search(r"([\d.,]+)\s*m²", str(detalles))
    if not m:
        return None
    val = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(val)
    except ValueError:
        return None


def parse_planta_idealista(detalles):
    m = re.search(r"(Bajo|Entreplanta|\d+ª)\s*planta", str(detalles), re.IGNORECASE)
    return m.group(0) if m else None


def parse_ascensor_idealista(detalles):
    d = str(detalles).lower()
    if "con ascensor" in d:
        return True
    if "sin ascensor" in d:
        return False
    return None


def parse_garaje_idealista(detalles):
    return "Garaje" in str(detalles)


def load_idealista():
    df = pd.read_csv(f"{RAW_DIR}/idealista_san_vicente_raw.csv", sep=";", dtype=str)
    df = df.dropna(subset=["precio"])
    out = pd.DataFrame(index=df.index)
    out["fuente"] = "idealista"
    out["precio_mes"] = df["precio"].apply(parse_precio)
    out["habitaciones"] = df["detalles"].apply(parse_habitaciones_idealista)
    out["m2"] = df["detalles"].apply(parse_m2_idealista)
    out["zona"] = None  # Idealista no da zona/barrio en el listado
    out["planta"] = df["detalles"].apply(parse_planta_idealista)
    out["ascensor"] = df["detalles"].apply(parse_ascensor_idealista)
    out["garaje"] = df["detalles"].apply(parse_garaje_idealista)
    out["tipo_alquiler"] = df["tag"].apply(
        lambda t: "temporada" if isinstance(t, str) and "temporada" in t.lower() else "anual/no_especificado"
    )
    out["texto_original"] = df["precio"].astype(str) + " | " + df["detalles"].astype(str)
    return out


def load_fotocasa():
    df = pd.read_csv(f"{RAW_DIR}/fotocasa_san_vicente_raw.csv", sep=";", dtype=str)
    df = df.dropna(subset=["precio"])
    out = pd.DataFrame(index=df.index)
    out["fuente"] = "fotocasa"
    out["precio_mes"] = df["precio"].apply(parse_precio)
    out["habitaciones"] = pd.to_numeric(df["habitaciones"], errors="coerce")
    out["m2"] = pd.to_numeric(df["m2"], errors="coerce")
    out["zona"] = df["zona"]
    out["planta"] = df["detalle"].apply(parse_planta_idealista)  # mismo patron de texto
    out["ascensor"] = df["detalle"].apply(
        lambda d: True if "ascensor" in str(d).lower() and "sin ascensor" not in str(d).lower() else None
    )
    out["garaje"] = False  # fotocasa no reporta garaje en el campo detalle capturado
    out["tipo_alquiler"] = df["tipo_alquiler"].apply(
        lambda t: "temporada" if isinstance(t, str) and t.strip() != "" else "anual/no_especificado"
    )
    out["texto_original"] = df["precio"].astype(str) + " | " + df["zona"].astype(str) + " | " + df["detalle"].astype(str)
    return out


def marcar_duplicados_cruzados(df):
    """
    Duplicado cruzado = mismo precio_mes, misma habitaciones y m2 muy similar (+-2 m2),
    apareciendo en fuentes distintas. No exigimos m2 exacto porque cada portal
    redondea/mide de forma distinta.
    Se conserva la primera fila (segun orden del dataframe) de cada grupo duplicado
    y se marca el resto.
    """
    df = df.copy()
    df["es_duplicado_cruzado"] = False
    df["m2_bin"] = (df["m2"] / 2).round() * 2  # agrupa m2 en bins de 2 para tolerar redondeos

    con_datos = df.dropna(subset=["precio_mes", "habitaciones", "m2_bin"])
    grupos = con_datos.groupby(["precio_mes", "habitaciones", "m2_bin"])
    for _, idx in grupos.groups.items():
        filas = df.loc[idx]
        if filas["fuente"].nunique() > 1 and len(filas) > 1:
            # hay mas de una fuente para la misma combinacion precio/hab/m2 -> duplicado cruzado
            primero = filas.index[0]
            resto = filas.index[1:]
            df.loc[resto, "es_duplicado_cruzado"] = True

    df = df.drop(columns=["m2_bin"])
    return df


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)

    idealista = load_idealista()
    fotocasa = load_fotocasa()

    combinado = pd.concat([idealista, fotocasa], ignore_index=True)
    combinado = marcar_duplicados_cruzados(combinado)

    out_path = f"{OUT_DIR}/alquiler_residencial_limpio.csv"
    combinado.to_csv(out_path, sep=";", index=False)

    n_total = len(combinado)
    n_dupes = combinado["es_duplicado_cruzado"].sum()
    print(f"Idealista: {len(idealista)} filas | Fotocasa: {len(fotocasa)} filas")
    print(f"Total combinado: {n_total} | Duplicados cruzados detectados: {n_dupes}")
    print(f"Filas unicas tras deduplicar: {n_total - n_dupes}")
    print(f"Guardado en: {out_path}")

    # sin precio o sin m2 no sirven para comparar -> los contamos aparte, no los borramos
    incompletos = combinado[combinado["precio_mes"].isna() | combinado["m2"].isna()]
    print(f"Filas con precio o m2 sin extraer (revisar manualmente): {len(incompletos)}")


if __name__ == "__main__":
    main()

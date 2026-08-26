"""
Limpieza conjunta de Idealista + Fotocasa (venta), San Vicente del Raspeig.
Misma logica que el script de alquiler: se limpian juntos porque es el mismo
mercado y puede haber el mismo inmueble publicado en los dos portales.

Salida: venta_limpio.csv con esquema unificado:
    fuente, precio, habitaciones, m2, precio_m2, zona, tipo_vivienda,
    es_duplicado_cruzado, es_outlier_lujo, texto_original
"""

import re
import os
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent
OUT_DIR = SCRIPT_DIR.parent / "limpio"


def parse_precio(txt):
    if pd.isna(txt) or txt == "":
        return None
    txt = str(txt).replace("€", "").strip()
    txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        return None


def parse_habitaciones(detalles):
    m = re.search(r"(\d+)\s*hab", str(detalles))
    return int(m.group(1)) if m else None


def parse_m2(detalles):
    m = re.search(r"([\d.,]+)\s*m²", str(detalles))
    if not m:
        return None
    val = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(val)
    except ValueError:
        return None


def tipo_vivienda_idealista(row):
    tag = str(row.get("tag", "")).lower()
    det = str(row.get("detalles", "")).lower()
    if "villa" in tag or "chalet" in det:
        return "chalet/villa"
    if "bungalow" in tag:
        return "bungalow"
    if "apartamento" in tag:
        return "apartamento"
    if "lujo" in tag:
        return "piso_lujo"
    return "piso"


def load_idealista():
    df = pd.read_csv(f"{RAW_DIR}/idealista_venta_san_vicente_raw.csv", sep=";", dtype=str)
    df = df.dropna(subset=["precio"])
    out = pd.DataFrame(index=df.index)
    out["fuente"] = "idealista"
    out["precio"] = df["precio"].apply(parse_precio)
    out["habitaciones"] = df["detalles"].apply(parse_habitaciones)
    out["m2"] = df["detalles"].apply(parse_m2)
    out["zona"] = None
    out["tipo_vivienda"] = df.apply(tipo_vivienda_idealista, axis=1)
    out["texto_original"] = df["precio"].astype(str) + " | " + df["detalles"].astype(str) + " | " + df["tag"].fillna("").astype(str)
    return out


def load_fotocasa():
    df = pd.read_csv(f"{RAW_DIR}/fotocasa_venta_san_vicente_raw.csv", sep=";", dtype=str)
    df = df.dropna(subset=["precio"])
    out = pd.DataFrame(index=df.index)
    out["fuente"] = "fotocasa"
    out["precio"] = df["precio"].apply(parse_precio)
    out["habitaciones"] = pd.to_numeric(df["habitaciones"], errors="coerce")
    out["m2"] = pd.to_numeric(df["m2"], errors="coerce")
    out["zona"] = df["zona"]
    out["tipo_vivienda"] = df["detalle"].apply(
        lambda d: "chalet/villa" if "piscina" in str(d).lower() and "trastero" in str(d).lower() else "piso"
    )
    out["texto_original"] = df["precio"].astype(str) + " | " + df["zona"].astype(str) + " | " + df["detalle"].astype(str)
    return out


def marcar_duplicados_cruzados(df):
    df = df.copy()
    df["es_duplicado_cruzado"] = False
    df["m2_bin"] = (df["m2"] / 5).round() * 5  # tolerancia mayor en venta (5 m2)
    con_datos = df.dropna(subset=["precio", "habitaciones", "m2_bin"])
    grupos = con_datos.groupby(["precio", "habitaciones", "m2_bin"])
    for _, idx in grupos.groups.items():
        filas = df.loc[idx]
        if filas["fuente"].nunique() > 1 and len(filas) > 1:
            resto = filas.index[1:]
            df.loc[resto, "es_duplicado_cruzado"] = True
    return df.drop(columns=["m2_bin"])


def marcar_outliers_lujo(df):
    """Marca (no borra) los precios que quedan muy por encima del rango tipico,
    para poder excluirlos facilmente del calculo de rentabilidad de un piso estandar."""
    df = df.copy()
    p95 = df["precio"].quantile(0.95)
    df["es_outlier_lujo"] = df["precio"] > p95
    return df


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    idealista = load_idealista()
    fotocasa = load_fotocasa()

    combinado = pd.concat([idealista, fotocasa], ignore_index=True)
    combinado["precio_m2"] = (combinado["precio"] / combinado["m2"]).round(0)
    combinado = marcar_duplicados_cruzados(combinado)
    combinado = marcar_outliers_lujo(combinado)

    out_path = f"{OUT_DIR}/venta_limpio.csv"
    combinado.to_csv(out_path, sep=";", index=False)

    n_total = len(combinado)
    n_dupes = combinado["es_duplicado_cruzado"].sum()
    n_lujo = combinado["es_outlier_lujo"].sum()
    print(f"Idealista: {len(idealista)} filas | Fotocasa: {len(fotocasa)} filas")
    print(f"Total combinado: {n_total} | Duplicados cruzados: {n_dupes} | Outliers de lujo (p95): {n_lujo}")
    print(f"Precio/m2 medio (sin excluir nada): {combinado['precio_m2'].mean():.0f} €/m2")
    print(f"Precio/m2 medio excluyendo duplicados y outliers de lujo: "
          f"{combinado[~combinado['es_duplicado_cruzado'] & ~combinado['es_outlier_lujo']]['precio_m2'].mean():.0f} €/m2")
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()

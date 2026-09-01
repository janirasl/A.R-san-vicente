"""
Limpieza y analisis de la captura turistica AMPLIADA (2026-09-01).

Motivo: la muestra anterior tenia n=7 para el precio/noche de vivienda
completa, insuficiente para deducir nada, y ademas mezclaba anuncios de
Alicante capital porque la busqueda de Airbnb por texto "San Vicente del
Raspeig" devuelve >1.000 alojamientos, casi todos fuera del municipio.

Que se hizo distinto en esta captura:
  1. Busqueda ACOTADA POR MAPA a las coordenadas del municipio
     (ne 38.43/-0.495, sw 38.375/-0.560) en vez de por texto -> solo entran
     alojamientos realmente dentro de San Vicente del Raspeig.
  2. Filtro "alojamiento entero" (entire_home) -> comparable a alquilar la
     vivienda completa, que es la estrategia que se esta modelando.
  3. TRES fechas distintas (feb / oct / jul) -> permite (a) mas observaciones
     y (b) medir la estacionalidad REAL de precio en vez de asumirla, ya que
     varias propiedades se repiten en las tres consultas.
  4. Booking como segunda fuente para el mismo municipio y fechas.

Salidas:
  - limpio/turistico_ampliado_limpio.csv
  - limpio/turistico_estacionalidad.csv  (misma propiedad en varias fechas)
  - limpio/turistico_comparables_arquetipo.csv (solo pisos comparables al
    arquetipo de 3 hab.)
"""

import os
import re
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent
OUT_DIR = SCRIPT_DIR.parent / "limpio"

# Tipos que NO son comparables a un piso estandar de 3 hab: producto distinto
# (villa/chalet con piscina para grupos grandes) o demasiado pequenos.
TIPOS_VILLA = {"Villa", "Chalet", "Adosado", "Casa rural"}

# El tipo que declara el portal no basta: Airbnb etiqueta "Vivienda" a
# "Villa Mulet con piscina exotica para 8 personas", que evidentemente NO es
# comparable a un piso estandar. Se mira tambien el nombre del anuncio.
PALABRAS_VILLA = ("villa", "chalet", "casa lulu", "casa abedul", "bungalow", "casa de campo", "casa rural")


def es_villa(row):
    nombre = str(row["nombre"]).lower()
    if any(p in nombre for p in PALABRAS_VILLA):
        return True
    if row["tipo_alojamiento"] in TIPOS_VILLA:
        return True
    return bool(row["dormitorios"] >= 5)


def cargar():
    df = pd.read_csv(RAW_DIR / "turistico_san_vicente_raw_2026-09-01.csv", sep=";", dtype=str)
    df["dormitorios"] = pd.to_numeric(df["dormitorios"], errors="coerce")
    df["camas"] = pd.to_numeric(df["camas"], errors="coerce")
    df["banos"] = pd.to_numeric(df["banos"], errors="coerce")
    df["m2"] = pd.to_numeric(df["m2"], errors="coerce")
    df["noches"] = pd.to_numeric(df["noches"], errors="coerce")
    df["precio_total_eur"] = pd.to_numeric(df["precio_total_eur"], errors="coerce")
    df["valoracion"] = pd.to_numeric(df["valoracion"], errors="coerce")
    df["num_valoraciones"] = pd.to_numeric(df["num_valoraciones"], errors="coerce")
    df["precio_noche"] = (df["precio_total_eur"] / df["noches"]).round(1)
    df["es_villa_o_chalet"] = df.apply(es_villa, axis=1)
    return df


def comparables_arquetipo(df):
    """
    Comparable al arquetipo del proyecto = piso/apartamento/vivienda entera,
    3-4 dormitorios, en San Vicente. Se excluyen villas y chalets (producto
    distinto: grupos grandes, piscina privada, precio por noche que no tiene
    nada que ver con alquilar un piso normal) y los loft/estudios de 1 dorm.
    """
    return df[(df["en_san_vicente"] == "si") &
              (~df["es_villa_o_chalet"]) &
              (df["dormitorios"].between(3, 4))].copy()


def estacionalidad(df):
    """Propiedades que aparecen en mas de una fecha -> variacion real de precio
    por temporada, medida sobre la MISMA vivienda (no comparando viviendas
    distintas entre si, que seria enganoso)."""
    sv = df[df["en_san_vicente"] == "si"]
    piv = sv.pivot_table(index=["nombre", "es_villa_o_chalet"], columns="temporada",
                         values="precio_noche", aggfunc="first")
    piv = piv.dropna(thresh=2)  # al menos 2 temporadas observadas
    if "alta (jul)" in piv.columns and "baja (feb)" in piv.columns:
        piv["variacion_jul_vs_feb_pct"] = ((piv["alta (jul)"] / piv["baja (feb)"] - 1) * 100).round(1)
    return piv.reset_index()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = cargar()

    sv = df[df["en_san_vicente"] == "si"]
    fuera = df[df["en_san_vicente"] != "si"]
    print(f"Observaciones totales de la captura: {len(df)}")
    print(f"  En San Vicente del Raspeig: {len(sv)}  |  Fuera del municipio (descartadas): {len(fuera)}")
    print(f"  Propiedades unicas en San Vicente: {sv['nombre'].nunique()}")
    print()

    print("--- Composicion del parque turistico de San Vicente (alojamiento entero) ---")
    comp = sv.drop_duplicates("nombre")
    print(comp.groupby("es_villa_o_chalet")["nombre"].count().rename(
        index={True: "villa/chalet/adosado (>=5 dorm o tipo villa)", False: "piso/apartamento/loft"}))
    print()
    print("Propiedades unicas por tipo:")
    print(comp.groupby("tipo_alojamiento")["nombre"].count())
    print()

    comparables = comparables_arquetipo(df)
    print("--- Comparables al arquetipo (piso entero de 3-4 dorm. en San Vicente) ---")
    print(comparables[["fuente", "temporada", "nombre", "dormitorios", "m2", "precio_noche"]].to_string(index=False))
    print()
    print(f"n comparables (observaciones): {len(comparables)}  |  propiedades unicas: {comparables['nombre'].nunique()}")
    if len(comparables):
        print(f"Precio/noche  mediana: {comparables['precio_noche'].median():.0f} EUR  "
              f"| media: {comparables['precio_noche'].mean():.0f} EUR  "
              f"| rango: {comparables['precio_noche'].min():.0f}-{comparables['precio_noche'].max():.0f} EUR")
        sin_piscina = comparables[~comparables["nombre"].str.contains("piscina", case=False, na=False)]
        print(f"Excluyendo el que tiene piscina en azotea (producto premium), n={len(sin_piscina)}: "
              f"mediana {sin_piscina['precio_noche'].median():.0f} EUR/noche "
              f"(rango {sin_piscina['precio_noche'].min():.0f}-{sin_piscina['precio_noche'].max():.0f})")
    print()

    est = estacionalidad(df)
    print("--- Estacionalidad REAL medida sobre la misma propiedad ---")
    print(est.to_string(index=False))
    print()

    df.to_csv(OUT_DIR / "turistico_ampliado_limpio.csv", sep=";", index=False)
    comparables.to_csv(OUT_DIR / "turistico_comparables_arquetipo.csv", sep=";", index=False)
    est.to_csv(OUT_DIR / "turistico_estacionalidad.csv", sep=";", index=False)
    print(f"Guardado en {OUT_DIR}: turistico_ampliado_limpio.csv | "
          f"turistico_comparables_arquetipo.csv | turistico_estacionalidad.csv")


if __name__ == "__main__":
    main()

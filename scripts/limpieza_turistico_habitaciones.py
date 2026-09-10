"""
Limpieza de la captura de HABITACIONES de Airbnb en San Vicente.

Por que existe este script (y no se mete en limpieza_turistico_ampliado.py):
Airbnb vende dos productos distintos bajo la misma marca, y hasta ahora el
proyecto solo media uno.

  - alojamiento entero -> compite con el alquiler residencial (piso completo)
  - habitacion privada -> compite con el alquiler por habitaciones de la UA

Mezclarlos da medias sin sentido: 43 EUR/noche de una habitacion y 145 EUR/noche
de un piso de 3 dormitorios no son el mismo precio de nada. De ahi que la salida
lleve una columna 'unidad' explicita y que el dataset unificado la propague.

Origen: raw/airbnb_habitaciones_san_vicente_2026-09-10.csv
  Busqueda acotada por coordenadas del municipio (no por texto: buscar
  "San Vicente del Raspeig" devuelve sobre todo Alicante capital), con filtro
  room_types=Private room, en dos fechas: 2026-07-06 (temporada alta) y
  2026-10-05 (curso). 11 anuncios unicos, cada uno observado en las dos fechas.

DOS MARCAS DE FIABILIDAD, que hay que respetar al analizar:

  a) 'dudoso_minimo_estancia' (2 anuncios): habitaciones con cama individual
     cuyo total de 5 noches sale a ~180 EUR/noche. Es casi seguro un minimo de
     estancia largo que Airbnb factura entero, no el precio real de 5 noches.
     Se conservan porque no esta comprobado, pero no entran en las medianas.

  b) 'estancia_alternativa' (3 observaciones): Airbnb devolvio un rango de
     fechas distinto al pedido (7 o 4 noches en vez de 5). El EUR/noche es
     correcto para SU rango, pero no es comparable en el analisis de
     estacionalidad, porque las tarifas cambian con la duracion.

Salidas:
  - limpio/turistico_habitaciones_limpio.csv
  - limpio/turistico_habitaciones_estacionalidad.csv  (misma habitacion, 2 fechas)
"""

import os
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent / "raw"
OUT_DIR = SCRIPT_DIR.parent / "limpio"

FICHERO = "airbnb_habitaciones_san_vicente_2026-09-10.csv"


def cargar():
    df = pd.read_csv(RAW_DIR / FICHERO, sep=";", dtype=str)
    for c in ["noches", "precio_total_eur", "precio_noche_eur", "valoracion",
              "num_valoraciones"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["id_anuncio"] = df["id_anuncio"].astype(str)
    df["en_san_vicente"] = df["en_san_vicente"].str.strip().str.lower()
    df["unidad"] = "habitacion"

    # el precio/noche se recalcula en vez de fiarse de la columna del raw:
    # asi cualquier error de transcripcion sale a la luz aqui y no mas abajo.
    calc = (df["precio_total_eur"] / df["noches"]).round(1)
    desvia = (calc - df["precio_noche_eur"]).abs() > 0.15
    if desvia.any():
        print(f"AVISO: {desvia.sum()} filas donde precio_total/noches no cuadra "
              f"con precio_noche_eur. Se usa el recalculado.")
    df["precio_noche"] = calc

    df["fiable"] = df["fiabilidad"] == "ok"
    df["es_comparable_arquetipo"] = (
        (df["en_san_vicente"] == "si") & df["fiable"]
    )
    return df


def estacionalidad(df):
    """Variacion de precio de LA MISMA habitacion entre julio y octubre.

    Solo con observaciones 'ok': una estancia de 7 noches frente a una de 5
    lleva otra tarifa, asi que compararlas mediria la duracion, no la estacion.
    """
    ok = df[(df["en_san_vicente"] == "si") & df["fiable"]]
    p = ok.pivot_table(index="id_anuncio", columns="fecha_estancia",
                       values="precio_noche", aggfunc="first")
    p = p.dropna()
    if p.shape[1] != 2:
        return pd.DataFrame()
    jul, oct_ = p.columns[0], p.columns[1]
    out = p.reset_index().rename(columns={jul: "precio_julio", oct_: "precio_octubre"})
    out["variacion_pct"] = ((out["precio_julio"] / out["precio_octubre"] - 1) * 100).round(1)
    out["identico"] = out["precio_julio"] == out["precio_octubre"]
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = cargar()

    sv = df[df["en_san_vicente"] == "si"]
    ok = sv[sv["fiable"]]

    print("=" * 78)
    print("HABITACIONES DE AIRBNB EN SAN VICENTE DEL RASPEIG")
    print("=" * 78)
    print(f"Observaciones ............ {len(df)}  (San Vicente: {len(sv)}, fuera: {len(df) - len(sv)})")
    print(f"Anuncios unicos en SVR ... {sv['id_anuncio'].nunique()}")
    print(f"  marcados no fiables .... {sv['id_anuncio'].nunique() - ok['id_anuncio'].nunique()}")
    print()

    print("--- Precio por noche, solo observaciones fiables ---")
    for fecha, g in ok.groupby("fecha_estancia"):
        p = g["precio_noche"]
        print(f"  {fecha}   n={len(g):2d}   mediana {p.median():6.1f}   "
              f"media {p.mean():6.1f}   rango {p.min():.1f}-{p.max():.1f}")
    print()

    est = estacionalidad(df)
    if len(est):
        print("--- Estacionalidad: misma habitacion en julio y en octubre ---")
        print(f"  habitaciones comparables ....... {len(est)}")
        print(f"  con precio IDENTICO al euro .... {int(est['identico'].sum())}")
        print(f"  variacion mediana .............. {est['variacion_pct'].median():+.1f}%")
        print()
        print("  Lectura: las habitaciones NO tienen prima de verano, igual que los")
        print("  pisos y al contrario que las villas (+75% en julio). Es la tercera")
        print("  fuente independiente que apunta a demanda universitaria, no de playa.")
        print()

    df.to_csv(OUT_DIR / "turistico_habitaciones_limpio.csv", sep=";", index=False)
    if len(est):
        est.to_csv(OUT_DIR / "turistico_habitaciones_estacionalidad.csv", sep=";", index=False)
    print(f"Guardado en {OUT_DIR}: turistico_habitaciones_limpio.csv | "
          f"turistico_habitaciones_estacionalidad.csv")

    print()
    print("RECORDATORIO para quien use estos datos: son 11 anuncios. Sirven para")
    print("situar el orden de magnitud del producto 'habitacion turistica' y para")
    print("medir su estacionalidad, NO para estimar la renta de una vivienda")
    print("concreta. Y los 11 son de anfitrion particular: casi todos alquilan una")
    print("habitacion del piso donde viven, que no es lo mismo que comprar un piso")
    print("y explotar sus 3 habitaciones por noches.")


if __name__ == "__main__":
    main()

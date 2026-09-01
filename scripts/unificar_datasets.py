"""
Une los CSV limpios de VIVIENDAS en un unico dataset largo (formato "tabla de
hechos"), para poder trabajar en Power BI con un solo fichero en vez de cinco.

Se pueden concatenar porque todos tienen el mismo grano: UNA FILA = UNA OFERTA
DE UNA VIVIENDA. Lo que cambia entre ellos es el mercado (alquiler, venta,
estudiantil, turistico) y la unidad del precio.

Clave del diseno: NO se mezclan unidades en la misma columna. Un alquiler de
990 EUR/mes y una venta de 237.950 EUR no pueden sumarse ni promediarse
juntos, asi que el precio va en TRES columnas separadas y excluyentes:
    precio_eur_mes | precio_eur_noche | precio_eur_venta
Asi, si en Power BI arrastras "precio_eur_mes" a un grafico, las filas de
venta y turistico simplemente no suman: es imposible calcular sin querer una
media que mezcle peras con manzanas.

Se incluye tambien el registro VUT (viviendas turisticas oficiales), que no
tiene precio, con tiene_precio = False, porque sirve para dimensionar la oferta
turistica del municipio. Filtra por esa columna si solo quieres precios.

NO se incluyen aqui las tablas de resultados del modelo (escenarios, punto de
equilibrio, supuestos): tienen otro grano (una fila = una estrategia o un
escenario, no una vivienda) y meterlas en la misma tabla seria un error de
modelado. Esas se importan aparte, son 3 ficheros pequenos.

Filtrando es_comparable_arquetipo = True, las medianas reproducen exactamente
los datos observados del modelo: 990 EUR/mes de alquiler, 292 EUR/mes por
habitacion y 237.950 EUR de compra. La unica diferencia esta en el turistico
(151 EUR/noche aqui frente a 145 en el modelo): esta columna marca los 3-4
dormitorios comparables, pero el modelo excluye ademas el piso con piscina en
azotea por ser producto premium. Si quieres reproducir el 145 exacto, filtra
tambien fuera la descripcion que contiene "piscina".

Salida: limpio/dataset_unificado.csv
"""

import os
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
LIMPIO_DIR = SCRIPT_DIR.parent / "limpio"

COLUMNAS = [
    "id", "mercado", "tipo_oferta", "fuente", "fecha_captura", "temporada",
    "habitaciones", "m2", "banos", "zona",
    "tiene_precio", "unidad_precio", "precio_eur_mes", "precio_eur_noche", "precio_eur_venta",
    "precio_por_m2", "es_comparable_arquetipo", "marca_calidad", "descripcion",
]


def base(n, mercado):
    df = pd.DataFrame(index=range(n))
    df["mercado"] = mercado
    for c in COLUMNAS:
        if c not in df.columns:
            df[c] = None
    return df


def cargar_alquiler():
    src = pd.read_csv(LIMPIO_DIR / "alquiler_residencial_limpio.csv", sep=";")
    df = base(len(src), "alquiler_residencial")
    df["tipo_oferta"] = src["tipo_alquiler"].values
    df["fuente"] = src["fuente"].values
    df["fecha_captura"] = src["fecha_captura"].values
    df["habitaciones"] = src["habitaciones"].values
    df["m2"] = src["m2"].values
    df["banos"] = src["banos"].values
    df["zona"] = src["zona"].values
    df["tiene_precio"] = True
    df["unidad_precio"] = "EUR/mes"
    df["precio_eur_mes"] = src["precio_mes"].values
    df["descripcion"] = src["texto_original"].values
    # m2 sospechoso: precio/m2 por debajo de 3 EUR/m2/mes es imposible -> error de la fuente
    ratio = src["precio_mes"] / src["m2"]
    df["marca_calidad"] = ["m2_sospechoso" if (pd.notna(r) and r < 3) else None for r in ratio]
    df["es_comparable_arquetipo"] = (
        (src["habitaciones"] == 3) & src["m2"].between(70, 130) &
        (src["tipo_alquiler"] == "anual/no_especificado") & (ratio >= 3)
    ).values
    return df


def cargar_venta():
    src = pd.read_csv(LIMPIO_DIR / "venta_limpio.csv", sep=";")
    df = base(len(src), "venta")
    df["tipo_oferta"] = src["tipo_vivienda"].values
    df["fuente"] = src["fuente"].values
    df["habitaciones"] = src["habitaciones"].values
    df["m2"] = src["m2"].values
    df["zona"] = src["zona"].values
    df["tiene_precio"] = True
    df["unidad_precio"] = "EUR (compra)"
    df["precio_eur_venta"] = src["precio"].values
    df["precio_por_m2"] = src["precio_m2"].values
    df["marca_calidad"] = ["outlier_lujo" if x else None for x in src["es_outlier_lujo"]]
    df["descripcion"] = src["texto_original"].values
    df["es_comparable_arquetipo"] = (
        (src["habitaciones"] == 3) & src["m2"].between(70, 130) & (~src["es_outlier_lujo"])
    ).values
    return df


def cargar_ua():
    src = pd.read_csv(LIMPIO_DIR / "ua_limpio.csv", sep=";")
    src = src[~src["es_duplicado"]].reset_index(drop=True)
    df = base(len(src), "estudiantil")
    df["tipo_oferta"] = src["tipo_oferta_simplificado"].values
    df["fuente"] = "UA Bolsa de Alojamiento"
    df["fecha_captura"] = src["fecha_oferta"].values
    df["habitaciones"] = src["habitaciones"].values
    df["zona"] = src["direccion"].values
    df["tiene_precio"] = True
    df["unidad_precio"] = "EUR/mes"
    df["precio_eur_mes"] = src["precio_num"].values
    df["descripcion"] = src["observaciones"].values
    # el arquetipo en estudiantil es la HABITACION suelta (es lo que se modela)
    df["es_comparable_arquetipo"] = (src["tipo_oferta_simplificado"] == "habitacion").values
    df["marca_calidad"] = [
        "clasificacion_heuristica" if "regimen A" in str(t) else None for t in src["tipo_oferta"]
    ]
    return df


def cargar_turistico():
    src = pd.read_csv(LIMPIO_DIR / "turistico_ampliado_limpio.csv", sep=";")
    df = base(len(src), "turistico")
    df["tipo_oferta"] = src["tipo_alojamiento"].values
    df["fuente"] = src["fuente"].values
    df["fecha_captura"] = src["fecha_captura"].values
    df["temporada"] = src["temporada"].values
    df["habitaciones"] = src["dormitorios"].values
    df["m2"] = src["m2"].values
    df["banos"] = src["banos"].values
    df["zona"] = src["municipio"].values
    df["tiene_precio"] = True
    df["unidad_precio"] = "EUR/noche"
    df["precio_eur_noche"] = src["precio_noche"].values
    df["descripcion"] = src["nombre"].values
    df["marca_calidad"] = [
        "villa_no_comparable" if v else ("fuera_del_municipio" if s != "si" else None)
        for v, s in zip(src["es_villa_o_chalet"], src["en_san_vicente"])
    ]
    df["es_comparable_arquetipo"] = (
        (src["en_san_vicente"] == "si") & (~src["es_villa_o_chalet"]) &
        src["dormitorios"].between(3, 4)
    ).values
    return df


def cargar_vut():
    src = pd.read_csv(LIMPIO_DIR / "vut_limpio.csv", sep=";")
    src = src[~src["es_duplicado"]].reset_index(drop=True)
    df = base(len(src), "vut_registro")
    df["tipo_oferta"] = "vivienda_uso_turistico_registrada"
    df["fuente"] = "Generalitat Valenciana (registro VUT)"
    df["fecha_captura"] = src["fecha_alta"].values
    df["habitaciones"] = src["dormitorios"].values
    df["m2"] = src["superficie_m2"].values
    df["zona"] = src["direccion"].values
    df["tiene_precio"] = False          # el registro oficial no publica precios
    df["unidad_precio"] = None
    df["descripcion"] = ("Registro VUT " + src["signatura"].astype(str)).values
    df["es_comparable_arquetipo"] = False
    return df


def main():
    partes = [cargar_alquiler(), cargar_venta(), cargar_ua(), cargar_turistico(), cargar_vut()]
    df = pd.concat(partes, ignore_index=True)

    # precio/m2 donde falta y se puede calcular (alquiler: EUR/m2/mes)
    falta = df["precio_por_m2"].isna() & df["m2"].notna() & df["precio_eur_mes"].notna()
    df.loc[falta, "precio_por_m2"] = (df.loc[falta, "precio_eur_mes"] / df.loc[falta, "m2"]).round(2)

    df["id"] = range(1, len(df) + 1)
    df = df[COLUMNAS]

    out = LIMPIO_DIR / "dataset_unificado.csv"
    df.to_csv(out, sep=";", index=False)

    print(f"Dataset unificado: {len(df)} filas x {len(df.columns)} columnas -> {out}\n")
    print("--- Filas por mercado ---")
    print(df["mercado"].value_counts().to_string())
    print()
    print("--- Filas comparables al arquetipo (columna es_comparable_arquetipo) ---")
    print(df[df["es_comparable_arquetipo"] == True]["mercado"].value_counts().to_string())
    print()
    print("--- Marcas de calidad (para excluir en Power BI si hace falta) ---")
    print(df["marca_calidad"].value_counts(dropna=True).to_string())
    print()
    print("--- Comprobacion: cada unidad de precio en su columna ---")
    print(df.groupby("unidad_precio")[["precio_eur_mes", "precio_eur_noche", "precio_eur_venta"]]
            .count().to_string())


if __name__ == "__main__":
    main()

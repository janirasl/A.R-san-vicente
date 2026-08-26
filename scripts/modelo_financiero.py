"""
Modelo financiero comparativo de las 4 estrategias, sobre UN MISMO arquetipo
de vivienda (para que la comparacion sea justa): piso de 3 habitaciones,
~90-100 m2, San Vicente del Raspeig. Es el piso mas representativo de la
muestra tanto en alquiler (66/144 = 46%) como en venta (31/99) y en UA piso
completo (10/17).

Metodologia (la tuya): ingresos brutos - gastos = ingresos netos -> ROI.
ROI aqui = ingreso neto anual / precio de compra del arquetipo (rentabilidad
neta anual sobre la inversion, sin financiacion/hipoteca).

Las 4 estrategias:
  1. Residencial anual  -> todo el año, piso completo, un solo inquilino/familia.
  2. Estudiantil x hab. -> todo el año, alquilado por habitaciones sueltas (UA).
  3. Turistico           -> todo el año, Airbnb/Booking, precio/noche x ocupacion.
  4. Mixto                -> 9 meses curso academico (estudiantil x hab.) +
                             3 meses verano (turistico). Es la estrategia mas
                             realista para una vivienda cerca de la UA: cubre el
                             hueco de demanda turistica/estudiantil que tiene
                             cada una por separado el resto del año.

TODOS los parametros de gasto/fiscalidad estan sacados de
resumen_recopilacion_datos.md (seccion 6) y quedan marcados como supuesto
('_ASUNCION') cuando la fuente da un rango en vez de una cifra unica, para que
se puedan cambiar facilmente sin tocar el resto del script.
"""

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
LIMPIO_DIR = SCRIPT_DIR.parent / "limpio"
EDA_DIR = SCRIPT_DIR.parent / "eda"
GRAF_DIR = SCRIPT_DIR.parent / "graficos"

# ---------------------------------------------------------------------------
# Supuestos / parametros (fuente: resumen_recopilacion_datos.md, seccion 6)
# ---------------------------------------------------------------------------
COMUNIDAD_MES = 70.0                 # ASUNCION: punto medio del rango 40-100 EUR/mes (piso estandar)
SEGURO_IMPAGO_PCT = 0.065            # ASUNCION: punto medio del rango 5-8% de la renta bruta anual
IBI_PCT_CATASTRAL = 0.00767          # dato oficial: tipo urbano San Vicente del Raspeig
RATIO_CATASTRAL_MERCADO = 0.55       # ASUNCION: valor catastral suele rondar 50-60% del valor de mercado
COMISION_TURISTICO_PCT = 0.10        # ASUNCION: punto medio entre Airbnb split-fee (~3%) y Booking (~15%)
OCUPACION_TURISTICA = 0.77           # proxy Alicante (INE no cubre San Vicente), ~281 noches/año
ITP_MAS_GASTOS_COMPRA_PCT = 0.11     # ASUNCION: punto medio del 10-12% (ITP 9% + notaria + registro + gestoria)
REDUCCION_IRPF_RESIDENCIAL = 0.50    # caso general, contratos posteriores a mayo 2023
REDUCCION_IRPF_TURISTICO = 0.0       # sin reduccion (capital inmobiliario puro)

MESES_CURSO = 9
MESES_VERANO = 3


def cargar_arquetipo():
    alq = pd.read_csv(LIMPIO_DIR / "alquiler_residencial_limpio.csv", sep=";")
    venta = pd.read_csv(LIMPIO_DIR / "venta_limpio.csv", sep=";")
    ua = pd.read_csv(LIMPIO_DIR / "ua_limpio.csv", sep=";")
    ua = ua[~ua["es_duplicado"]]
    turistico = pd.read_csv(LIMPIO_DIR / "turistico_precios_limpio.csv", sep=";")

    arquetipo_alq = alq[(alq["habitaciones"] == 3) & (alq["m2"].between(70, 130)) &
                         (alq["tipo_alquiler"] == "anual/no_especificado")]
    arquetipo_venta = venta[(venta["habitaciones"] == 3) & (venta["m2"].between(70, 130)) &
                             (~venta["es_outlier_lujo"])]

    precio_compra = arquetipo_venta["precio"].median()
    precio_residencial_mes = arquetipo_alq["precio_mes"].median()
    precio_habitacion_mes = ua[ua["tipo_oferta_simplificado"] == "habitacion"]["precio_num"].median()
    precio_noche_turistico = turistico[turistico["categoria"] == "vivienda_completa"]["precio_noche"].median()

    print("--- Arquetipo: piso 3 hab. / 70-130 m2, San Vicente del Raspeig ---")
    print(f"Precio de compra (mediana venta, n={len(arquetipo_venta)}): {precio_compra:,.0f} EUR")
    print(f"Alquiler residencial anual (mediana, n={len(arquetipo_alq)}): {precio_residencial_mes:,.0f} EUR/mes")
    print(f"Alquiler por habitacion UA (mediana, n={(ua['tipo_oferta_simplificado']=='habitacion').sum()}): {precio_habitacion_mes:,.0f} EUR/hab./mes")
    print(f"Precio/noche turistico vivienda completa (mediana, n={(turistico['categoria']=='vivienda_completa').sum()}): {precio_noche_turistico:,.0f} EUR/noche")
    print()

    return {
        "precio_compra": precio_compra,
        "precio_residencial_mes": precio_residencial_mes,
        "precio_habitacion_mes": precio_habitacion_mes,
        "precio_noche_turistico": precio_noche_turistico,
    }


def gastos_fijos_anuales(precio_compra):
    """Gastos que aplican TODOS los años, independientemente de la estrategia."""
    ibi = precio_compra * RATIO_CATASTRAL_MERCADO * IBI_PCT_CATASTRAL
    comunidad = COMUNIDAD_MES * 12
    return ibi, comunidad


def calcular_estrategias(datos):
    precio_compra = datos["precio_compra"]
    ibi, comunidad = gastos_fijos_anuales(precio_compra)
    gastos_fijos = ibi + comunidad

    filas = []

    # 1. Residencial anual (piso completo, todo el año)
    bruto = datos["precio_residencial_mes"] * 12
    seguro_impago = bruto * SEGURO_IMPAGO_PCT
    neto = bruto - gastos_fijos - seguro_impago
    base_irpf = neto * (1 - REDUCCION_IRPF_RESIDENCIAL)
    filas.append(dict(estrategia="1. Residencial anual", ingreso_bruto=bruto,
                       gastos=gastos_fijos + seguro_impago, ingreso_neto=neto,
                       base_imponible_irpf=base_irpf, roi_neto=neto / precio_compra))

    # 2. Estudiantil por habitacion (3 hab., todo el año)
    bruto = datos["precio_habitacion_mes"] * 3 * 12
    seguro_impago = bruto * SEGURO_IMPAGO_PCT
    neto = bruto - gastos_fijos - seguro_impago
    base_irpf = neto * (1 - REDUCCION_IRPF_RESIDENCIAL)
    filas.append(dict(estrategia="2. Estudiantil x habitacion", ingreso_bruto=bruto,
                       gastos=gastos_fijos + seguro_impago, ingreso_neto=neto,
                       base_imponible_irpf=base_irpf, roi_neto=neto / precio_compra))

    # 3. Turistico (todo el año, Airbnb/Booking)
    bruto = datos["precio_noche_turistico"] * 30.4 * OCUPACION_TURISTICA * 12
    comision = bruto * COMISION_TURISTICO_PCT
    neto = bruto - gastos_fijos - comision
    base_irpf = neto * (1 - REDUCCION_IRPF_TURISTICO)
    filas.append(dict(estrategia="3. Turistico (Airbnb/Booking)", ingreso_bruto=bruto,
                       gastos=gastos_fijos + comision, ingreso_neto=neto,
                       base_imponible_irpf=base_irpf, roi_neto=neto / precio_compra))

    # 4. Mixto: 9 meses estudiantil x hab. + 3 meses turistico (verano)
    bruto_curso = datos["precio_habitacion_mes"] * 3 * MESES_CURSO
    bruto_verano = datos["precio_noche_turistico"] * 30.4 * OCUPACION_TURISTICA * MESES_VERANO
    bruto = bruto_curso + bruto_verano
    seguro_impago_curso = bruto_curso * SEGURO_IMPAGO_PCT
    comision_verano = bruto_verano * COMISION_TURISTICO_PCT
    neto = bruto - gastos_fijos - seguro_impago_curso - comision_verano
    # aproximacion: se prorratea la reduccion IRPF solo sobre la parte residencial
    base_irpf = (neto * (bruto_curso / bruto)) * (1 - REDUCCION_IRPF_RESIDENCIAL) + \
                (neto * (bruto_verano / bruto)) * (1 - REDUCCION_IRPF_TURISTICO)
    filas.append(dict(estrategia="4. Mixto (9m estudiantil + 3m turistico)", ingreso_bruto=bruto,
                       gastos=gastos_fijos + seguro_impago_curso + comision_verano, ingreso_neto=neto,
                       base_imponible_irpf=base_irpf, roi_neto=neto / precio_compra))

    df = pd.DataFrame(filas)
    df["ingreso_neto_mes"] = df["ingreso_neto"] / 12
    df["yield_bruto"] = df["ingreso_bruto"] / precio_compra
    df["payback_anos"] = precio_compra / df["ingreso_neto"]
    return df, gastos_fijos, ibi, comunidad


def main():
    os.makedirs(EDA_DIR, exist_ok=True)
    datos = cargar_arquetipo()
    df, gastos_fijos, ibi, comunidad = calcular_estrategias(datos)

    precio_compra = datos["precio_compra"]
    gastos_compra = precio_compra * ITP_MAS_GASTOS_COMPRA_PCT

    print(f"Gastos fijos anuales (IBI estimado {ibi:,.0f} EUR + comunidad {comunidad:,.0f} EUR): {gastos_fijos:,.0f} EUR/año")
    print(f"Gastos de compra (ITP + notaria + registro + gestoria, {ITP_MAS_GASTOS_COMPRA_PCT:.0%}): {gastos_compra:,.0f} EUR (pago unico)")
    print()

    cols_mostrar = ["estrategia", "ingreso_bruto", "gastos", "ingreso_neto",
                     "ingreso_neto_mes", "yield_bruto", "roi_neto", "payback_anos"]
    tabla = df[cols_mostrar].copy()
    tabla["ingreso_bruto"] = tabla["ingreso_bruto"].round(0)
    tabla["gastos"] = tabla["gastos"].round(0)
    tabla["ingreso_neto"] = tabla["ingreso_neto"].round(0)
    tabla["ingreso_neto_mes"] = tabla["ingreso_neto_mes"].round(0)
    tabla["yield_bruto"] = (tabla["yield_bruto"] * 100).round(2)
    tabla["roi_neto"] = (tabla["roi_neto"] * 100).round(2)
    tabla["payback_anos"] = tabla["payback_anos"].round(1)
    print(tabla.to_string(index=False))

    ganador = df.loc[df["roi_neto"].idxmax()]
    print(f"\n>>> Mayor ROI neto (antes de IRPF): {ganador['estrategia']} — {ganador['roi_neto']*100:.2f}% anual")

    print("\n--- Efecto fiscal (base imponible IRPF, sin reduccion en turistico) ---")
    for _, row in df.iterrows():
        print(f"  {row['estrategia']}: base imponible {row['base_imponible_irpf']:,.0f} EUR "
              f"(vs. ingreso neto {row['ingreso_neto']:,.0f} EUR)")
    df["ratio_base_irpf"] = df["base_imponible_irpf"] / df["ingreso_neto"]
    ganador_fiscal = df.loc[df["ratio_base_irpf"].idxmin()]
    print(f"  -> Menor base imponible en proporcion al neto: {ganador_fiscal['estrategia']} "
          f"(mejor tratamiento fiscal relativo)")

    out_path = EDA_DIR / "comparativa_estrategias.csv"
    df.to_csv(out_path, sep=";", index=False)
    print(f"\nTabla completa guardada en: {out_path}")

    graficar_comparativa(df)


def graficar_comparativa(df):
    os.makedirs(GRAF_DIR, exist_ok=True)
    labels = [e.split(". ")[1] for e in df["estrategia"]]
    colors = ["#3b6ea5", "#e0a020", "#3ba55d", "#8a4fb5"]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    axes[0].bar(labels, df["roi_neto"] * 100, color=colors)
    axes[0].set_title("ROI neto anual por estrategia\n(arquetipo 3 hab. / ~90-100 m2, antes de IRPF)")
    axes[0].set_ylabel("% anual")
    axes[0].tick_params(axis="x", rotation=20)
    for i, v in enumerate(df["roi_neto"] * 100):
        axes[0].text(i, v + 0.2, f"{v:.1f}%", ha="center")

    axes[1].bar(labels, df["ingreso_neto_mes"], color=colors)
    axes[1].set_title("Ingreso NETO mensual por estrategia")
    axes[1].set_ylabel("EUR/mes")
    axes[1].tick_params(axis="x", rotation=20)
    for i, v in enumerate(df["ingreso_neto_mes"]):
        axes[1].text(i, v + 20, f"{v:.0f}€", ha="center")

    fig.tight_layout()
    out_path = GRAF_DIR / "06_comparativa_neta_roi.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Grafico guardado en: {out_path}")


if __name__ == "__main__":
    main()

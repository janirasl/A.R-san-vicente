"""
SENSIBILIDAD A LA ESTACIONALIDAD: ¿cuanto depende el modelo mixto de que el
verano sea temporada alta para un PISO?

El problema que resuelve este script:
serie_temporal_estrategias.py asume que la ocupacion turistica del piso sigue
una curva con pico en agosto, con una amplitud de +/-20 puntos porcentuales.
Esa amplitud me la invente. Y la estrategia MIXTA se apoya entera en ese
supuesto: su logica es "curso academico por habitaciones + verano turistico",
o sea, que el verano compensa por ser temporada alta.

Pero la captura turistica de 2026-09-01 midio la estacionalidad de PRECIO sobre
las mismas propiedades en tres fechas, y el resultado va en contra:

    Villa Sensation Seasons (10 dorm.)     feb 1.006 -> jul 1.765   +75%
    Villa Mulet (3 dorm., piscina)         feb   271 -> jul   351   +30%
    Alojamiento rural con piscina          feb   157 -> jul   180   +15%
    Bungalow Navarro                       feb   163 -> jul   163     0%
    Apartamento 4 dorm.                    feb   151 -> oct   150    -1%
    Loft junto a la Universidad            feb   105 -> oct    91   -13%

Las villas suben mucho en verano. Los PISOS no suben nada, e incluso bajan. Y
el arquetipo del proyecto es un piso.

Matiz importante y honesto: lo medido es estacionalidad de PRECIO, no de
OCUPACION. No son lo mismo. Pero si la demanda de verano fuera fuerte, lo
normal seria que el precio respondiera, como hace en las villas. Que el piso
mantenga precio plano todo el año sugiere que su demanda no tiene un pico
estival marcado — probablemente porque en San Vicente el turismo de piso no es
de playa sino universitario (familias de visita, profesorado, congresos), que
se reparte de otro modo.

Es una inferencia, no una medicion. Pero esta mejor fundada que el +/-20 que
puse yo sin ningun apoyo.

Este script cuantifica cuanto cambia el resultado segun la amplitud asumida.

Salidas:
  - eda/sensibilidad_estacionalidad.csv
  - graficos/12_sensibilidad_estacionalidad.png
"""

import os
from math import cos, pi
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from modelo_financiero import (
    cargar_arquetipo, gastos_fijos_anuales, gastos_operativos_turistico,
    ESCENARIOS, SEGURO_IMPAGO_PCT, ITP_MAS_GASTOS_COMPRA_PCT,
    MESES_ACADEMICOS, N_MESES_CURSO, N_MESES_VERANO,
    OCUPACION_RESIDENCIAL, OCUPACION_ESTUDIANTIL_CURSO, OCUPACION_ESTUDIANTIL_VERANO,
)

SCRIPT_DIR = Path(__file__).resolve().parent
EDA_DIR = SCRIPT_DIR.parent / "eda"
GRAF_DIR = SCRIPT_DIR.parent / "graficos"

ESCENARIO = "base"

# Amplitudes a comparar (puntos porcentuales de ocupacion sobre la media anual)
AMPLITUDES = {
    "0,20 — supuesto original (sin apoyo)": 0.20,
    "0,10 — intermedio": 0.10,
    "0,05 — coherente con el precio plano de los pisos": 0.05,
    "0,00 — sin estacionalidad": 0.00,
}

MESES_VERANO_CAL = [7, 8]  # jul-ago


def ocupacion_mes(mes_cal, media, amplitud):
    """Curva coseno centrada en agosto. La media anual no cambia con la
    amplitud (la integral del coseno en un periodo completo es cero), asi que
    lo unico que se mueve es el REPARTO entre meses."""
    oc = media + amplitud * cos(2 * pi * (mes_cal - 8) / 12)
    return min(max(oc, 0.05), 0.98)


def evaluar(datos, amplitud):
    esc = ESCENARIOS[ESCENARIO]
    precio_compra = datos["precio_compra"]
    inversion_total = precio_compra * (1 + ITP_MAS_GASTOS_COMPRA_PCT)
    ibi, comunidad = gastos_fijos_anuales(precio_compra)
    gastos_fijos = ibi + comunidad

    # --- Turistico puro: la media anual no cambia, asi que su total tampoco.
    #     Se recalcula mes a mes para dejarlo explicito.
    bruto_tur = 0.0
    op_tur = 0.0
    for m in range(1, 13):
        oc = ocupacion_mes(m, esc["ocupacion"], amplitud)
        bruto_tur += datos["precio_noche_turistico"] * 30.4 * oc
        op, _ = gastos_operativos_turistico(datos, esc, oc, meses=1)
        op_tur += op
    neto_tur = bruto_tur - gastos_fijos - op_tur

    # --- Mixto: SOLO cobra turistico en jul-ago, justo los meses del pico.
    #     Por eso es la estrategia sensible a la amplitud.
    bruto_curso = datos["precio_habitacion_mes"] * 3 * N_MESES_CURSO * OCUPACION_ESTUDIANTIL_CURSO
    bruto_verano = 0.0
    op_verano = 0.0
    for m in MESES_VERANO_CAL:
        oc = ocupacion_mes(m, esc["ocupacion"], amplitud)
        bruto_verano += datos["precio_noche_turistico"] * 30.4 * oc
        op, _ = gastos_operativos_turistico(datos, esc, oc, meses=1)
        op_verano += op
    bruto_mix = bruto_curso + bruto_verano
    neto_mix = bruto_mix - gastos_fijos - bruto_curso * SEGURO_IMPAGO_PCT - op_verano

    oc_media_verano = sum(ocupacion_mes(m, esc["ocupacion"], amplitud) for m in MESES_VERANO_CAL) / 2

    return dict(
        amplitud=amplitud,
        ocupacion_verano=round(oc_media_verano, 3),
        turistico_neto=round(neto_tur),
        turistico_roi=neto_tur / inversion_total,
        mixto_neto=round(neto_mix),
        mixto_roi=neto_mix / inversion_total,
    )


def referencias(datos):
    precio_compra = datos["precio_compra"]
    inversion_total = precio_compra * (1 + ITP_MAS_GASTOS_COMPRA_PCT)
    ibi, comunidad = gastos_fijos_anuales(precio_compra)
    gastos_fijos = ibi + comunidad

    bruto_r = datos["precio_residencial_mes"] * 12 * OCUPACION_RESIDENCIAL
    neto_r = bruto_r - gastos_fijos - bruto_r * SEGURO_IMPAGO_PCT

    bruto_e = (datos["precio_habitacion_mes"] * 3 * N_MESES_CURSO * OCUPACION_ESTUDIANTIL_CURSO +
               datos["precio_habitacion_mes"] * 3 * N_MESES_VERANO * OCUPACION_ESTUDIANTIL_VERANO)
    neto_e = bruto_e - gastos_fijos - bruto_e * SEGURO_IMPAGO_PCT

    return neto_r / inversion_total, neto_e / inversion_total


def main():
    os.makedirs(EDA_DIR, exist_ok=True)
    os.makedirs(GRAF_DIR, exist_ok=True)
    datos = cargar_arquetipo(verbose=False)
    roi_resid, roi_estud = referencias(datos)

    filas = []
    for etiqueta, amp in AMPLITUDES.items():
        r = evaluar(datos, amp)
        r["escenario_amplitud"] = etiqueta
        filas.append(r)
    df = pd.DataFrame(filas)

    print("=" * 84)
    print("¿CUANTO DEPENDE EL MODELO DE QUE EL VERANO SEA TEMPORADA ALTA PARA UN PISO?")
    print("=" * 84)
    print(f"Escenario de costes: {ESCENARIO} | ocupacion media anual: {ESCENARIOS[ESCENARIO]['ocupacion']:.0%}")
    print(f"Referencias fijas: residencial {roi_resid*100:.2f}% | estudiantil {roi_estud*100:.2f}%\n")

    tabla = df[["escenario_amplitud", "ocupacion_verano", "turistico_roi", "mixto_roi"]].copy()
    tabla["turistico_roi"] = (tabla["turistico_roi"] * 100).round(2)
    tabla["mixto_roi"] = (tabla["mixto_roi"] * 100).round(2)
    tabla["ocupacion_verano"] = (tabla["ocupacion_verano"] * 100).round(1)
    tabla.columns = ["amplitud asumida", "ocup. jul-ago (%)", "ROI turistico (%)", "ROI mixto (%)"]
    print(tabla.to_string(index=False))
    print()

    orig = df[df["amplitud"] == 0.20].iloc[0]
    real = df[df["amplitud"] == 0.05].iloc[0]

    print("-" * 84)
    print("LECTURA")
    print("-" * 84)
    print(f"El TURISTICO puro apenas se mueve ({orig['turistico_roi']*100:.2f}% -> {real['turistico_roi']*100:.2f}%).")
    print("  Logico: cobra los 12 meses, y la curva solo redistribuye ocupacion entre meses")
    print("  sin cambiar la media anual. Lo que gana en agosto lo pierde en febrero.\n")
    print(f"El MIXTO si se mueve: {orig['mixto_roi']*100:.2f}% -> {real['mixto_roi']*100:.2f}% "
          f"({(real['mixto_roi']-orig['mixto_roi'])*100:+.2f} puntos).")
    print("  Porque solo cobra turistico en julio y agosto: si esos dos meses dejan de ser")
    print("  el pico, la estrategia pierde justo su razon de ser.\n")

    if orig["mixto_roi"] > roi_resid >= real["mixto_roi"]:
        print(">>> CAMBIO DE CONCLUSION")
        print(f"    Con la amplitud original (0,20), el mixto batia al residencial")
        print(f"    ({orig['mixto_roi']*100:.2f}% frente a {roi_resid*100:.2f}%).")
        print(f"    Con una amplitud coherente con lo medido (0,05), ya NO lo bate")
        print(f"    ({real['mixto_roi']*100:.2f}% frente a {roi_resid*100:.2f}%).")
        print("    La ventaja del modelo mixto dependia de un supuesto sin apoyo empirico.")
    else:
        print(">>> El orden entre mixto y residencial no cambia con la amplitud.")
        print(f"    mixto {real['mixto_roi']*100:.2f}% vs residencial {roi_resid*100:.2f}%")

    df.to_csv(EDA_DIR / "sensibilidad_estacionalidad.csv", sep=";", index=False)
    print(f"\nGuardado en {EDA_DIR / 'sensibilidad_estacionalidad.csv'}")

    graficar(df, roi_resid, roi_estud)


def graficar(df, roi_resid, roi_estud):
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    x = df["amplitud"] * 100

    ax.plot(x, df["mixto_roi"] * 100, marker="o", color="#8a4fb5", linewidth=2,
            label="Mixto (curso + verano turístico)")
    ax.plot(x, df["turistico_roi"] * 100, marker="s", color="#3ba55d", linewidth=2,
            label="Turístico puro")
    ax.axhline(roi_resid * 100, color="#3b6ea5", linestyle="--", linewidth=2,
               label=f"Residencial anual ({roi_resid*100:.2f}%)")
    ax.axhline(roi_estud * 100, color="#e0a020", linestyle=":", linewidth=2,
               label=f"Estudiantil ({roi_estud*100:.2f}%)")

    ax.axvspan(0, 7, color="#3ba55d", alpha=0.07)
    ax.text(3.5, ax.get_ylim()[0] + 0.15, "rango coherente con\nel precio plano medido",
            fontsize=7.5, ha="center", color="#2c6b4f")

    ax.set_xlabel("Amplitud estacional asumida (puntos porcentuales de ocupación sobre la media)")
    ax.set_ylabel("ROI neto anual (%) sobre inversión total")
    ax.set_title("La ventaja del modelo mixto depende de un supuesto que los datos no respaldan\n"
                 "San Vicente del Raspeig — escenario de costes base")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    ax.invert_xaxis()
    fig.tight_layout()
    out = GRAF_DIR / "12_sensibilidad_estacionalidad.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print(f"Grafico guardado en: {out}")


if __name__ == "__main__":
    main()

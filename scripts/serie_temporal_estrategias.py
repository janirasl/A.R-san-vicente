"""
Serie temporal mensual de las 4 estrategias, pensada para exportar a Power BI.

Responde dos preguntas que el modelo anual (modelo_financiero.py) no contesta
por si solo:
  1. En que EPOCA DEL AÑO es mas rentable cada estrategia (estacionalidad).
  2. A PARTIR DE CUANTO TIEMPO cada estrategia toma ventaja sobre las demas,
     contando que ninguna vivienda esta alquilada el 100% del tiempo (ni
     siquiera el residencial o el estudiantil, no solo el turistico).

Diferencia clave respecto al modelo anual: aqui TODAS las estrategias llevan
un supuesto de ocupacion/vacancia, no solo el turistico:
  - Residencial anual: vacancia por cambio de inquilino (95% ocupacion, plano
    todo el año) -> ASUNCION, no hay dato real de rotacion de inquilinos.
  - Estudiantil x habitacion: ocupacion alta en curso academico (sep-jun) y
    baja en verano (jul-ago), porque la demanda universitaria desaparece esos
    meses -> ASUNCION basada en el calendario academico, no en datos UA reales
    de estacionalidad (la UA solo dio una foto fija de la oferta, no series
    temporales).
  - Turistico: curva estacional (pico en verano) calibrada para que la MEDIA
    anual siga siendo el 77% ya usado y documentado (proxy Alicante) -> la
    FORMA estacional en si es una asuncion adicional, no hay datos mensuales
    reales de Airbnb/Booking para San Vicente, solo precios puntuales.
  - Mixto: usa la ocupacion de estudiantil en curso y de turistico en verano.

Salidas (carpeta powerbi/, listas para importar en Power BI):
  - flujo_mensual_estrategias.csv : una fila por estrategia x mes (10 años)
  - cruces_entre_estrategias.csv  : a partir de que mes cada estrategia supera
                                     (en ingreso neto acumulado) a cada otra
"""

import os
from math import cos, pi
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from modelo_financiero import (
    cargar_arquetipo, gastos_fijos_anuales,
    SEGURO_IMPAGO_PCT, COMISION_TURISTICO_PCT, ITP_MAS_GASTOS_COMPRA_PCT,
    OCUPACION_TURISTICA,
)

SCRIPT_DIR = Path(__file__).resolve().parent
GRAF_DIR = SCRIPT_DIR.parent / "graficos"
PBI_DIR = SCRIPT_DIR.parent / "powerbi"

N_ANIOS = 30  # suficiente para que el payback de las 4 estrategias sea visible (residencial ronda 26 años)
N_MESES = N_ANIOS * 12
FECHA_INICIO = pd.Timestamp("2026-09-01")  # primer mes tras la compra (supuesto)

# --- Supuestos de ocupacion/vacancia por estrategia (NUEVOS respecto al modelo anual) ---
OCUPACION_RESIDENCIAL = 0.95   # ASUNCION: ~18 dias/año vacios por cambio de inquilino
MESES_ACADEMICOS = {9, 10, 11, 12, 1, 2, 3, 4, 5, 6}  # sep-jun
OCUPACION_ESTUDIANTIL_CURSO = 0.95   # ASUNCION: casi siempre ocupado en curso
OCUPACION_ESTUDIANTIL_VERANO = 0.30  # ASUNCION: la mayoria de estudiantes se va en verano
AMPLITUD_ESTACIONAL_TURISTICO = 0.20  # ASUNCION: +/-20 puntos sobre la media anual, pico en agosto


def ocupacion_turistica_mes(mes_calendario):
    """Curva estacional (coseno) centrada en agosto (mes 8), con media anual
    exacta = OCUPACION_TURISTICA (la integral de un coseno en un periodo
    completo es 0, asi que el promedio de los 12 meses no cambia)."""
    fase = 2 * pi * (mes_calendario - 8) / 12
    oc = OCUPACION_TURISTICA + AMPLITUD_ESTACIONAL_TURISTICO * cos(fase)
    return min(max(oc, 0.05), 0.98)


def ocupacion_estudiantil_mes(mes_calendario):
    return OCUPACION_ESTUDIANTIL_CURSO if mes_calendario in MESES_ACADEMICOS else OCUPACION_ESTUDIANTIL_VERANO


def construir_flujo_mensual(datos):
    precio_compra = datos["precio_compra"]
    ibi, comunidad = gastos_fijos_anuales(precio_compra)
    gastos_fijos_mes = (ibi + comunidad) / 12

    filas = []
    for m_abs in range(1, N_MESES + 1):
        fecha = FECHA_INICIO + pd.DateOffset(months=m_abs - 1)
        mes_cal = fecha.month
        anio = (m_abs - 1) // 12 + 1

        # 1. Residencial anual
        oc = OCUPACION_RESIDENCIAL
        bruto = datos["precio_residencial_mes"] * oc
        seguro = bruto * SEGURO_IMPAGO_PCT
        neto = bruto - gastos_fijos_mes - seguro
        filas.append(dict(estrategia="1. Residencial anual", mes_absoluto=m_abs, anio=anio,
                           mes_calendario=mes_cal, fecha=fecha, ocupacion_asumida=oc,
                           ingreso_bruto=bruto, gastos=gastos_fijos_mes + seguro, ingreso_neto=neto))

        # 2. Estudiantil x habitacion (3 hab.)
        oc = ocupacion_estudiantil_mes(mes_cal)
        bruto = datos["precio_habitacion_mes"] * 3 * oc
        seguro = bruto * SEGURO_IMPAGO_PCT
        neto = bruto - gastos_fijos_mes - seguro
        filas.append(dict(estrategia="2. Estudiantil x habitacion", mes_absoluto=m_abs, anio=anio,
                           mes_calendario=mes_cal, fecha=fecha, ocupacion_asumida=oc,
                           ingreso_bruto=bruto, gastos=gastos_fijos_mes + seguro, ingreso_neto=neto))

        # 3. Turistico (Airbnb/Booking)
        oc = ocupacion_turistica_mes(mes_cal)
        bruto = datos["precio_noche_turistico"] * 30.4 * oc
        comision = bruto * COMISION_TURISTICO_PCT
        neto = bruto - gastos_fijos_mes - comision
        filas.append(dict(estrategia="3. Turistico (Airbnb/Booking)", mes_absoluto=m_abs, anio=anio,
                           mes_calendario=mes_cal, fecha=fecha, ocupacion_asumida=oc,
                           ingreso_bruto=bruto, gastos=gastos_fijos_mes + comision, ingreso_neto=neto))

        # 4. Mixto: curso -> estudiantil x hab. | verano -> turistico
        if mes_cal in MESES_ACADEMICOS:
            oc = ocupacion_estudiantil_mes(mes_cal)
            bruto = datos["precio_habitacion_mes"] * 3 * oc
            gasto_var = bruto * SEGURO_IMPAGO_PCT
        else:
            oc = ocupacion_turistica_mes(mes_cal)
            bruto = datos["precio_noche_turistico"] * 30.4 * oc
            gasto_var = bruto * COMISION_TURISTICO_PCT
        neto = bruto - gastos_fijos_mes - gasto_var
        filas.append(dict(estrategia="4. Mixto (curso+verano)", mes_absoluto=m_abs, anio=anio,
                           mes_calendario=mes_cal, fecha=fecha, ocupacion_asumida=oc,
                           ingreso_bruto=bruto, gastos=gastos_fijos_mes + gasto_var, ingreso_neto=neto))

    df = pd.DataFrame(filas)
    df["ingreso_neto_acumulado"] = df.groupby("estrategia")["ingreso_neto"].cumsum()

    gastos_compra = precio_compra * ITP_MAS_GASTOS_COMPRA_PCT
    inversion_inicial = precio_compra + gastos_compra
    df["balance_acumulado"] = df["ingreso_neto_acumulado"] - inversion_inicial
    df["roi_acumulado"] = df["ingreso_neto_acumulado"] / precio_compra
    return df, inversion_inicial


def calcular_cruces(df):
    """Para cada par de estrategias, en que mes el ingreso neto ACUMULADO de
    una supera de forma definitiva a la otra (busca el ultimo cambio de signo,
    no el primero, por si hay cruces temporales por estacionalidad antes de
    que una tome ventaja de forma estable)."""
    estrategias = df["estrategia"].unique()
    pivote = df.pivot(index="mes_absoluto", columns="estrategia", values="ingreso_neto_acumulado")

    filas = []
    for i, a in enumerate(estrategias):
        for b in estrategias[i + 1:]:
            diff = pivote[a] - pivote[b]
            signo = diff.apply(lambda x: 1 if x > 0 else -1)
            cambios = signo[signo != signo.shift(1)].index.tolist()
            if len(cambios) <= 1:
                filas.append(dict(estrategia_a=a, estrategia_b=b, hay_cruce=False, mes_cruce=None,
                                   anio_cruce=None, ganador=(a if diff.iloc[-1] > 0 else b)))
            else:
                ultimo_cruce = cambios[-1]
                filas.append(dict(estrategia_a=a, estrategia_b=b, hay_cruce=True, mes_cruce=int(ultimo_cruce),
                                   anio_cruce=round(ultimo_cruce / 12, 1),
                                   ganador=(a if diff.loc[ultimo_cruce] > 0 else b)))
    return pd.DataFrame(filas)


def calcular_payback(df):
    """Mes en el que el balance acumulado (ingreso neto acumulado - inversion
    inicial) cruza cero por primera vez para cada estrategia -- cuando esa
    estrategia, por si sola, ha recuperado lo invertido."""
    filas = []
    for est, g in df.groupby("estrategia"):
        g = g.sort_values("mes_absoluto")
        positivos = g[g["balance_acumulado"] >= 0]
        if positivos.empty:
            filas.append(dict(estrategia=est, mes_payback=None, anio_payback=None))
        else:
            mes = int(positivos.iloc[0]["mes_absoluto"])
            filas.append(dict(estrategia=est, mes_payback=mes, anio_payback=round(mes / 12, 1)))
    return pd.DataFrame(filas)


def graficar(df):
    os.makedirs(GRAF_DIR, exist_ok=True)
    colors = {"1. Residencial anual": "#3b6ea5", "2. Estudiantil x habitacion": "#e0a020",
              "3. Turistico (Airbnb/Booking)": "#3ba55d", "4. Mixto (curso+verano)": "#8a4fb5"}

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    ciclo = df[df["anio"] == 1]
    for est, g in ciclo.groupby("estrategia"):
        axes[0].plot(g["mes_calendario"], g["ingreso_neto"], marker="o", label=est.split(". ")[1], color=colors[est])
    axes[0].set_title("Estacionalidad: ingreso neto mensual por estrategia\n(ciclo de 12 meses)")
    axes[0].set_xlabel("Mes del año")
    axes[0].set_ylabel("EUR/mes")
    axes[0].set_xticks(range(1, 13))
    axes[0].legend(fontsize=8)

    for est, g in df.groupby("estrategia"):
        axes[1].plot(g["mes_absoluto"] / 12, g["ingreso_neto_acumulado"], label=est.split(". ")[1], color=colors[est])
    axes[1].set_title(f"Ingreso neto ACUMULADO a {N_ANIOS} años\n(incl. vacancia/estacionalidad en las 4 estrategias)")
    axes[1].set_xlabel("Años desde la compra")
    axes[1].set_ylabel("EUR acumulados")
    axes[1].legend(fontsize=8)

    fig.tight_layout()
    out_path = GRAF_DIR / "08_serie_temporal_estrategias.png"
    fig.savefig(out_path)
    plt.close(fig)
    print(f"Grafico guardado en: {out_path}")


def main():
    os.makedirs(PBI_DIR, exist_ok=True)
    datos = cargar_arquetipo()
    df, inversion_inicial = construir_flujo_mensual(datos)

    flujo_path = PBI_DIR / "flujo_mensual_estrategias.csv"
    df.to_csv(flujo_path, index=False)
    print(f"Flujo mensual ({len(df)} filas, {N_ANIOS} años x 4 estrategias) guardado en: {flujo_path}")

    cruces = calcular_cruces(df)
    cruces_path = PBI_DIR / "cruces_entre_estrategias.csv"
    cruces.to_csv(cruces_path, index=False)
    print(f"\nInversion inicial (compra + gastos de compra): {inversion_inicial:,.0f} EUR\n")
    print("--- Cuando toma ventaja cada estrategia (ingreso neto acumulado) ---")
    for _, row in cruces.iterrows():
        nombre_a, nombre_b = row["estrategia_a"].split(". ")[1], row["estrategia_b"].split(". ")[1]
        ganador = row["ganador"].split(". ")[1]
        if not row["hay_cruce"]:
            print(f"  {nombre_a} vs {nombre_b}: {ganador} gana desde el mes 1 (nunca se cruzan)")
        else:
            print(f"  {nombre_a} vs {nombre_b}: cruce definitivo en el mes {row['mes_cruce']} "
                  f"(año {row['anio_cruce']}), gana {ganador}")
    print(f"\nTabla de cruces guardada en: {cruces_path}")

    payback = calcular_payback(df)
    payback_path = PBI_DIR / "payback_por_estrategia.csv"
    payback.to_csv(payback_path, index=False)
    print(f"\n--- Payback (recuperar la inversion inicial de {inversion_inicial:,.0f} EUR) por estrategia sola ---")
    for _, row in payback.iterrows():
        nombre = row["estrategia"].split(". ")[1]
        if pd.isna(row["mes_payback"]):
            print(f"  {nombre}: no recupera la inversion en {N_ANIOS} años")
        else:
            print(f"  {nombre}: mes {int(row['mes_payback'])} (año {row['anio_payback']})")
    print(f"Tabla de payback guardada en: {payback_path}")

    graficar(df)


if __name__ == "__main__":
    main()

"""
PUNTO DE EQUILIBRIO EN NOCHES: cuantas noches al mes tiene que estar alquilado
el piso en turistico para igualar a cada alternativa.

Por que este enfoque es mejor que el de escenarios:
  El modelo de escenarios parte de "asumo una ocupacion del X%" y calcula el
  ROI. Pero la ocupacion es justo el dato que NO tenemos de San Vicente del
  Raspeig -> la conclusion acababa dependiendo de una cifra inventada.

  Aqui se invierte la pregunta: se parte SOLO de precios observados (alquiler
  residencial, precio/habitacion, precio/noche turistico, precio de compra) y
  se DESPEJA cuantas noches hacen falta. La ocupacion deja de ser un supuesto
  de entrada y pasa a ser el resultado: "hacen falta N noches al mes; juzga tu
  si eso es alcanzable en este municipio".

  Lo unico que sigue siendo supuesto es la ESTRUCTURA DE COSTES. Por eso se
  calcula tambien un CASO SUELO que usa exclusivamente el unico coste
  documentado (la comision de plataforma) e ignora limpieza, suministros,
  gestion y mantenimiento. Ese suelo es un limite inferior real: el numero de
  noches necesarias nunca puede ser MENOR que ese, pase lo que pase con los
  costes. Es la cifra mas defendible de todo el analisis.

Salidas:
  - eda/punto_equilibrio_noches.csv
  - graficos/10_punto_equilibrio_noches.png
"""

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from modelo_financiero import (
    cargar_arquetipo, gastos_fijos_anuales, ESCENARIOS,
    SEGURO_IMPAGO_PCT, ITP_MAS_GASTOS_COMPRA_PCT,
    N_MESES_CURSO, N_MESES_VERANO,
    OCUPACION_RESIDENCIAL, OCUPACION_ESTUDIANTIL_CURSO, OCUPACION_ESTUDIANTIL_VERANO,
)

SCRIPT_DIR = Path(__file__).resolve().parent
EDA_DIR = SCRIPT_DIR.parent / "eda"
GRAF_DIR = SCRIPT_DIR.parent / "graficos"

# Caso suelo: SOLO el coste documentado (comision de plataforma). Se usa el 12%
# del escenario base, que sale de las tarifas publicadas de Booking (~15%) y
# Airbnb split-fee (~3%). Todo lo demas se pone a cero -> limite inferior.
CASO_SUELO = dict(comision_pct=0.12, gestion_pct=0.0, mantenimiento_pct=0.0,
                  limpieza_por_estancia=0.0, noches_por_estancia=4.0, suministros_mes=0.0)


def neto_mensual_turistico(datos, costes, noches_mes, gastos_fijos_mes):
    """Ingreso neto mensual del turistico en funcion de las NOCHES OCUPADAS."""
    bruto = datos["precio_noche_turistico"] * noches_mes
    variable_pct = costes["comision_pct"] + costes["gestion_pct"] + costes["mantenimiento_pct"]
    limpieza_por_noche = (costes["limpieza_por_estancia"] / costes["noches_por_estancia"]
                          if costes["noches_por_estancia"] else 0.0)
    return bruto * (1 - variable_pct) - limpieza_por_noche * noches_mes - costes["suministros_mes"] - gastos_fijos_mes


def noches_necesarias(datos, costes, objetivo_neto_mes, gastos_fijos_mes):
    """Despeje analitico: neto(n) es lineal en n, asi que se resuelve directo."""
    variable_pct = costes["comision_pct"] + costes["gestion_pct"] + costes["mantenimiento_pct"]
    limpieza_por_noche = (costes["limpieza_por_estancia"] / costes["noches_por_estancia"]
                          if costes["noches_por_estancia"] else 0.0)
    margen_por_noche = datos["precio_noche_turistico"] * (1 - variable_pct) - limpieza_por_noche
    if margen_por_noche <= 0:
        return None
    fijos = costes["suministros_mes"] + gastos_fijos_mes
    return (objetivo_neto_mes + fijos) / margen_por_noche


def netos_alternativas(datos, gastos_fijos_anual):
    """Ingreso neto MENSUAL de las alternativas, todo con precios observados."""
    # Residencial
    bruto_r = datos["precio_residencial_mes"] * 12 * OCUPACION_RESIDENCIAL
    neto_r = bruto_r - gastos_fijos_anual - bruto_r * SEGURO_IMPAGO_PCT

    # Estudiantil por habitacion (curso + verano)
    bruto_e = (datos["precio_habitacion_mes"] * 3 * N_MESES_CURSO * OCUPACION_ESTUDIANTIL_CURSO +
               datos["precio_habitacion_mes"] * 3 * N_MESES_VERANO * OCUPACION_ESTUDIANTIL_VERANO)
    neto_e = bruto_e - gastos_fijos_anual - bruto_e * SEGURO_IMPAGO_PCT

    return {
        "Residencial anual": neto_r / 12,
        "Estudiantil x habitacion": neto_e / 12,
        "Cubrir gastos (ROI 0)": 0.0,
    }


def main():
    os.makedirs(EDA_DIR, exist_ok=True)
    os.makedirs(GRAF_DIR, exist_ok=True)
    datos = cargar_arquetipo(verbose=False)

    precio_compra = datos["precio_compra"]
    ibi, comunidad = gastos_fijos_anuales(precio_compra)
    gastos_fijos_anual = ibi + comunidad
    gastos_fijos_mes = gastos_fijos_anual / 12

    print("=" * 82)
    print("PUNTO DE EQUILIBRIO EN NOCHES — cuantas noches/mes necesita el turistico")
    print("=" * 82)
    print("Todo parte de precios OBSERVADOS:")
    print(f"  precio/noche turistico ..... {datos['precio_noche_turistico']:>7,.0f} EUR   (n={datos['n_turistico']})")
    print(f"  alquiler residencial ....... {datos['precio_residencial_mes']:>7,.0f} EUR/mes (n={datos['n_residencial']})")
    print(f"  alquiler por habitacion .... {datos['precio_habitacion_mes']:>7,.0f} EUR/mes (n={datos['n_habitacion']})")
    print(f"  precio de compra ........... {precio_compra:>7,.0f} EUR   (n={datos['n_compra']})")
    print()

    objetivos = netos_alternativas(datos, gastos_fijos_anual)
    print("Objetivo a batir (ingreso neto mensual de cada alternativa):")
    for k, v in objetivos.items():
        print(f"  {k:<26} {v:>8,.0f} EUR/mes")
    print()

    estructuras = {"SUELO (solo comision documentada)": CASO_SUELO}
    estructuras.update({f"costes {k}": v for k, v in ESCENARIOS.items()})

    filas = []
    for nombre_est, costes in estructuras.items():
        for nombre_obj, objetivo in objetivos.items():
            n = noches_necesarias(datos, costes, objetivo, gastos_fijos_mes)
            if n is None:
                filas.append(dict(estructura_costes=nombre_est, objetivo=nombre_obj,
                                  noches_mes=None, noches_ano=None, ocupacion_equivalente=None))
                continue
            filas.append(dict(estructura_costes=nombre_est, objetivo=nombre_obj,
                              noches_mes=round(n, 1), noches_ano=round(n * 12),
                              ocupacion_equivalente=round(n / 30.4, 3)))
    df = pd.DataFrame(filas)

    for nombre_est in estructuras:
        sub = df[df["estructura_costes"] == nombre_est]
        print("-" * 82)
        print(nombre_est.upper())
        for _, r in sub.iterrows():
            if pd.isna(r["noches_mes"]):
                print(f"  Para igualar a {r['objetivo']:<26}: IMPOSIBLE (el margen por noche es negativo)")
            else:
                print(f"  Para igualar a {r['objetivo']:<26}: {r['noches_mes']:>5.1f} noches/mes "
                      f"({r['noches_ano']:>3.0f} al año, {r['ocupacion_equivalente']:.1%} de ocupacion)")
    print()

    suelo = df[(df["estructura_costes"] == "SUELO (solo comision documentada)") &
               (df["objetivo"] == "Residencial anual")].iloc[0]
    peor = df[(df["estructura_costes"] == "costes pesimista") &
              (df["objetivo"] == "Residencial anual")].iloc[0]
    print("=" * 82)
    print("LECTURA")
    print("=" * 82)
    print(f"Para que el turistico bata al alquiler residencial hacen falta, como MINIMO ABSOLUTO,")
    print(f"{suelo['noches_mes']:.1f} noches al mes ({suelo['noches_ano']:.0f} al año). Ese suelo ignora limpieza,")
    print("suministros, gestion y mantenimiento: es imposible bajar de ahi, pase lo que pase")
    print("con los costes, y no depende de ninguna cifra inventada.")
    print(f"Con la estructura de costes mas cara de las modeladas subiria a {peor['noches_mes']:.1f} noches/mes")
    print(f"({peor['noches_ano']:.0f} al año).")
    print()
    print("La pregunta que queda, y que estos datos NO responden, es si un piso de 3 hab. en")
    print("San Vicente del Raspeig consigue ese numero de noches. Para saberlo haria falta")
    print("mirar la disponibilidad real de los pisos que ya operan alli.")

    df.to_csv(EDA_DIR / "punto_equilibrio_noches.csv", sep=";", index=False)
    print(f"\nGuardado en {EDA_DIR / 'punto_equilibrio_noches.csv'}")

    graficar(datos, estructuras, objetivos, gastos_fijos_mes)


def graficar(datos, estructuras, objetivos, gastos_fijos_mes):
    fig, ax = plt.subplots(figsize=(10, 5.5))
    noches = list(range(0, 31))
    colores = {"SUELO (solo comision documentada)": "#000000", "costes pesimista": "#a53b3b",
               "costes base": "#3b6ea5", "costes optimista": "#3ba55d"}

    for nombre, costes in estructuras.items():
        netos = [neto_mensual_turistico(datos, costes, n, gastos_fijos_mes) for n in noches]
        estilo = "--" if nombre.startswith("SUELO") else "-"
        ax.plot(noches, netos, estilo, label=nombre, color=colores[nombre])

    ax.axhline(objetivos["Residencial anual"], color="#e0a020", linewidth=2,
               label=f"Residencial anual ({objetivos['Residencial anual']:.0f} EUR/mes)")
    ax.axhline(objetivos["Estudiantil x habitacion"], color="#8a4fb5", linewidth=2, linestyle=":",
               label=f"Estudiantil ({objetivos['Estudiantil x habitacion']:.0f} EUR/mes)")
    ax.axhline(0, color="gray", linewidth=0.8)

    ax.set_xlabel("Noches alquiladas al mes")
    ax.set_ylabel("Ingreso neto (EUR/mes)")
    ax.set_title("¿Cuantas noches al mes necesita el turistico para batir a cada alternativa?\n"
                 f"(precio/noche observado: {datos['precio_noche_turistico']:.0f} EUR, n={datos['n_turistico']})")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = GRAF_DIR / "10_punto_equilibrio_noches.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"Grafico guardado en: {out}")


if __name__ == "__main__":
    main()

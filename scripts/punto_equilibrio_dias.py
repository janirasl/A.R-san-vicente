"""
PUNTO DE EQUILIBRIO EN NOCHES: cuantas noches al mes hay que alquilar por dias
para igualar a cada alternativa de largo plazo.

Por que este enfoque es mejor que el de escenarios:
  El modelo de escenarios parte de "asumo una ocupacion del X%" y calcula el
  ROI. Pero la ocupacion es justo el dato que NO tenemos de San Vicente del
  Raspeig -> la conclusion acababa dependiendo de una cifra inventada.

  Aqui se invierte la pregunta: se parte SOLO de precios observados y se
  DESPEJA cuantas noches hacen falta. La ocupacion deja de ser un supuesto de
  entrada y pasa a ser el resultado: "hacen falta N noches al mes; juzga tu si
  eso es alcanzable en este municipio".

  Lo unico que sigue siendo supuesto es la ESTRUCTURA DE COSTES. Por eso se
  calcula tambien un CASO SUELO que usa exclusivamente el unico coste
  documentado (la comision de plataforma) e ignora limpieza, suministros,
  gestion y mantenimiento. Ese suelo es un limite inferior real: el numero de
  noches necesarias nunca puede ser MENOR que ese, pase lo que pase con los
  costes. Es la cifra mas defendible de todo el analisis.

QUE HAY DE NUEVO EN ESTA VERSION
  Alquilar por dias no es una cosa, son dos: se puede poner por noches el PISO
  ENTERO o las TRES HABITACIONES por separado. Son productos con precio y
  costes distintos, asi que el umbral tambien es distinto, y ahora se calculan
  los dos frente a los dos modos de largo plazo. Cuatro respuestas donde antes
  habia dos.

COMO SE MIDEN LAS NOCHES (importante para leer la tabla)
  "Noches al mes" significa lo mismo en las dos modalidades: noches ocupadas
  POR UNIDAD ALQUILADA. En piso entero es el piso; en habitaciones es cada una
  de las tres. Asi 10 noches/mes es el mismo 33% de ocupacion en ambos casos y
  las cifras se pueden comparar directamente.

  Coherente con el modelo financiero: para la misma ocupacion, tres
  habitaciones generan el TRIPLE de estancias (y de limpiezas y check-ins) que
  el piso entero, aunque cada limpieza salga mas barata.

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
    SEGURO_IMPAGO_PCT,
    N_MESES_CURSO, N_MESES_VERANO,
    OCUPACION_RESIDENCIAL, OCUPACION_ESTUDIANTIL_CURSO, OCUPACION_ESTUDIANTIL_VERANO,
    N_HABITACIONES_ARQUETIPO, RATIO_LIMPIEZA_HABITACION,
)

SCRIPT_DIR = Path(__file__).resolve().parent
EDA_DIR = SCRIPT_DIR.parent / "eda"
GRAF_DIR = SCRIPT_DIR.parent / "graficos"

# Caso suelo: SOLO el coste documentado (comision de plataforma). Se usa el 12%
# del escenario base, que sale de las tarifas publicadas de Booking (~15%) y
# Airbnb split-fee (~3%). Todo lo demas se pone a cero -> limite inferior.
CASO_SUELO = dict(comision_pct=0.12, gestion_pct=0.0, mantenimiento_pct=0.0,
                  limpieza_por_estancia=0.0, noches_por_estancia=4.0, suministros_mes=0.0)


def modalidades(datos):
    """Las dos formas de alquilar por noches, con lo que las diferencia.

    n_unidades      cuantas cosas se alquilan a la vez (1 piso, o 3 habitaciones)
    ratio_limpieza  lo que cuesta limpiar una unidad frente al piso entero
    """
    m = {
        "piso entero": dict(
            precio_noche=datos["precio_noche_turistico"],
            n_unidades=1,
            ratio_limpieza=1.0,
            n_muestra=datos["n_turistico"],
        ),
    }
    if datos.get("precio_habitacion_noche") is not None:
        m["3 habitaciones"] = dict(
            precio_noche=datos["precio_habitacion_noche"],
            n_unidades=N_HABITACIONES_ARQUETIPO,
            ratio_limpieza=RATIO_LIMPIEZA_HABITACION,
            n_muestra=datos["n_habitacion_noche"],
        )
    return m


def margen_por_noche(mod, costes):
    """Lo que deja cada noche ocupada, ya descontados los costes variables."""
    variable_pct = costes["comision_pct"] + costes["gestion_pct"] + costes["mantenimiento_pct"]
    limpieza_noche = (
        mod["n_unidades"] * mod["ratio_limpieza"] * costes["limpieza_por_estancia"]
        / costes["noches_por_estancia"] if costes["noches_por_estancia"] else 0.0
    )
    bruto_noche = mod["precio_noche"] * mod["n_unidades"]
    return bruto_noche * (1 - variable_pct) - limpieza_noche


def neto_mensual(mod, costes, noches_mes, gastos_fijos_mes):
    """Ingreso neto mensual en funcion de las NOCHES OCUPADAS por unidad."""
    return (margen_por_noche(mod, costes) * noches_mes
            - costes["suministros_mes"] - gastos_fijos_mes)


def noches_necesarias(mod, costes, objetivo_neto_mes, gastos_fijos_mes):
    """Despeje analitico: el neto es lineal en las noches, se resuelve directo."""
    m = margen_por_noche(mod, costes)
    if m <= 0:
        return None
    fijos = costes["suministros_mes"] + gastos_fijos_mes
    return (objetivo_neto_mes + fijos) / m


def netos_alternativas(datos, gastos_fijos_anual):
    """Ingreso neto MENSUAL de las alternativas de largo plazo, con precios observados."""
    bruto_r = datos["precio_residencial_mes"] * 12 * OCUPACION_RESIDENCIAL
    neto_r = bruto_r - gastos_fijos_anual - bruto_r * SEGURO_IMPAGO_PCT

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

    mods = modalidades(datos)

    print("=" * 88)
    print("PUNTO DE EQUILIBRIO EN NOCHES — las dos formas de alquilar por dias")
    print("=" * 88)
    print("Todo parte de precios OBSERVADOS:")
    print(f"  precio/noche piso entero ....... {datos['precio_noche_turistico']:>7,.0f} EUR   (n={datos['n_turistico']})")
    if "3 habitaciones" in mods:
        print(f"  precio/noche habitacion ........ {datos['precio_habitacion_noche']:>7,.0f} EUR   (n={datos['n_habitacion_noche']})")
    print(f"  alquiler residencial ........... {datos['precio_residencial_mes']:>7,.0f} EUR/mes (n={datos['n_residencial']})")
    print(f"  alquiler por habitacion (UA) ... {datos['precio_habitacion_mes']:>7,.0f} EUR/mes (n={datos['n_habitacion']})")
    print(f"  precio de compra ............... {precio_compra:>7,.0f} EUR   (n={datos['n_compra']})")
    print()
    print("Las noches se cuentan POR UNIDAD ALQUILADA, asi que 10 noches/mes es el mismo")
    print("33% de ocupacion tanto para el piso entero como para cada habitacion.")
    print()

    objetivos = netos_alternativas(datos, gastos_fijos_anual)
    print("Objetivo a batir (ingreso neto mensual de cada alternativa de largo plazo):")
    for k, v in objetivos.items():
        print(f"  {k:<26} {v:>8,.0f} EUR/mes")
    print()

    estructuras = {"SUELO (solo comision documentada)": CASO_SUELO}
    estructuras.update({f"costes {k}": v for k, v in ESCENARIOS.items()})

    filas = []
    for nombre_mod, mod in mods.items():
        for nombre_est, costes in estructuras.items():
            for nombre_obj, objetivo in objetivos.items():
                n = noches_necesarias(mod, costes, objetivo, gastos_fijos_mes)
                filas.append(dict(
                    modalidad=nombre_mod, estructura_costes=nombre_est, objetivo=nombre_obj,
                    noches_mes=None if n is None else round(n, 1),
                    noches_ano=None if n is None else round(n * 12),
                    ocupacion_equivalente=None if n is None else round(n / 30.4, 3),
                ))
    df = pd.DataFrame(filas)

    for nombre_mod in mods:
        print("=" * 88)
        print(f"MODALIDAD: {nombre_mod.upper()}")
        print("=" * 88)
        for nombre_est in estructuras:
            sub = df[(df["modalidad"] == nombre_mod) & (df["estructura_costes"] == nombre_est)]
            print("-" * 88)
            print(f"  {nombre_est}")
            for _, r in sub.iterrows():
                if pd.isna(r["noches_mes"]):
                    print(f"    Para igualar a {r['objetivo']:<26}: IMPOSIBLE (margen por noche negativo)")
                else:
                    print(f"    Para igualar a {r['objetivo']:<26}: {r['noches_mes']:>5.1f} noches/mes "
                          f"({r['noches_ano']:>3.0f} al año, {r['ocupacion_equivalente']:.1%} de ocupacion)")
        print()

    lectura(df, mods)

    df.to_csv(EDA_DIR / "punto_equilibrio_noches.csv", sep=";", index=False)
    print(f"\nGuardado en {EDA_DIR / 'punto_equilibrio_noches.csv'}")

    graficar(mods, estructuras, objetivos, gastos_fijos_mes)


def suelo_de(df, modalidad, objetivo="Residencial anual"):
    f = df[(df["modalidad"] == modalidad) &
           (df["estructura_costes"] == "SUELO (solo comision documentada)") &
           (df["objetivo"] == objetivo)]
    return f.iloc[0] if len(f) else None


def lectura(df, mods):
    print("=" * 88)
    print("LECTURA")
    print("=" * 88)
    s_piso = suelo_de(df, "piso entero")
    print(f"Piso entero: hacen falta como MINIMO ABSOLUTO {s_piso['noches_mes']:.1f} noches al mes "
          f"({s_piso['noches_ano']:.0f} al año)")
    print("para batir al alquiler residencial. Ese suelo ignora limpieza, suministros, gestion")
    print("y mantenimiento: es imposible bajar de ahi, y no depende de ninguna cifra inventada.")

    if "3 habitaciones" in mods:
        s_hab = suelo_de(df, "3 habitaciones")
        print()
        print(f"Tres habitaciones: {s_hab['noches_mes']:.1f} noches al mes POR HABITACION "
              f"({s_hab['noches_ano']:.0f} al año, {s_hab['ocupacion_equivalente']:.1%}).")
        dif = (s_hab["noches_mes"] / s_piso["noches_mes"] - 1) * 100
        print(f"Es un {abs(dif):.0f}% {'MAS' if dif > 0 else 'MENOS'} que el piso entero, y ademas hay que")
        print("conseguirlo TRES veces en paralelo: son tres calendarios que llenar, no uno.")
        print()
        print("Conclusion practica: por noches, el piso entero exige menos ocupacion y menos")
        print("gestion para el mismo resultado. Trocear la vivienda en habitaciones solo tiene")
        print("sentido si se cree que las tres se llenan bastante mas que el piso completo,")
        print("y eso este trabajo no lo ha medido.")

    print()
    print("La pregunta que estos datos NO responden sigue siendo la misma: si un piso de 3 hab.")
    print("en San Vicente consigue ese numero de noches. Para saberlo haria falta seguir la")
    print("disponibilidad real de los pocos pisos que ya operan alli.")


def graficar(mods, estructuras, objetivos, gastos_fijos_mes):
    n_mod = len(mods)
    fig, axes = plt.subplots(1, n_mod, figsize=(6.2 * n_mod, 5.5), squeeze=False,
                             sharey=True)  # mismo eje Y: si no, comparar los dos paneles engaña
    noches = list(range(0, 31))
    colores = {"SUELO (solo comision documentada)": "#000000", "costes pesimista": "#a53b3b",
               "costes base": "#3b6ea5", "costes optimista": "#3ba55d"}

    for ax, (nombre_mod, mod) in zip(axes[0], mods.items()):
        for nombre_est, costes in estructuras.items():
            y = [neto_mensual(mod, costes, n, gastos_fijos_mes) for n in noches]
            ax.plot(noches, y, label=nombre_est, color=colores.get(nombre_est),
                    lw=2.2 if "SUELO" in nombre_est else 1.5,
                    ls="--" if "SUELO" in nombre_est else "-")

        for nombre_obj, objetivo in objetivos.items():
            if objetivo <= 0:
                continue
            ax.axhline(objetivo, color="#888888", ls=":", lw=1)
            ax.text(0.4, objetivo, f" {nombre_obj}: {objetivo:,.0f} EUR/mes",
                    fontsize=7.5, va="bottom", color="#555555")

        ax.axhline(0, color="#333333", lw=0.8)
        ax.set_title(f"Por noches: {nombre_mod}\n(n={mod['n_muestra']} comparables observados)", fontsize=10)
        ax.set_xlabel("Noches ocupadas al mes, por unidad alquilada")
        ax.set_ylabel("Ingreso neto (EUR/mes)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7.5, loc="upper left")

    fig.suptitle("¿Cuántas noches hacen falta para batir al alquiler de largo plazo?\n"
                 "San Vicente del Raspeig · arquetipo de 3 habitaciones · solo precios observados",
                 fontsize=11.5)
    fig.tight_layout()
    out = GRAF_DIR / "10_punto_equilibrio_noches.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print(f"Grafico guardado en: {out}")


if __name__ == "__main__":
    main()

"""
Modelo financiero comparativo de las 4 estrategias, sobre UN MISMO arquetipo
de vivienda: piso de 3 habitaciones, ~90-100 m2, San Vicente del Raspeig.

Metodologia: ingresos brutos - gastos = ingresos netos -> ROI.

PRINCIPIO DE ESTE SCRIPT: separar siempre DATOS OBSERVADOS de SUPUESTOS.
  - BLOQUE 1 (DATOS OBSERVADOS): sale de los CSV limpios del proyecto, cada
    cifra con su tamaño de muestra (n). Es lo unico que se puede defender como
    "dato de San Vicente del Raspeig".
  - BLOQUE 2 (SUPUESTOS): hipotesis del modelo. NO son datos. Ninguna procede
    de una medicion local; van con su justificacion y su rango. Se exportan a
    eda/supuestos_modelo.csv para que en Power BI se vean como lo que son.

Por eso las conclusiones de este script son CONDICIONALES: no dicen "el
turistico rinde un X%", dicen "bajo un escenario de ocupacion del X% y unos
costes operativos de Y, el modelo estima Z%".

Las 4 estrategias (todas sobre el mismo piso, mismo precio de compra):
  1. Residencial anual  -> todo el año, piso completo, un inquilino.
  2. Estudiantil x hab. -> por habitaciones; curso academico (sep-jun) con
     ocupacion alta y verano (jul-ago) con ocupacion baja. NO se asume que
     los estudiantes paguen 12 meses: esa era una distorsion del modelo
     anterior que inflaba esta estrategia.
  3. Turistico          -> Airbnb/Booking, precio/noche x ocupacion, con los
     costes operativos reales del vacacional (limpieza por estancia,
     suministros a cargo del propietario, mantenimiento/reposicion, gestion
     y comision de plataforma).
  4. Mixto              -> curso academico por habitaciones + verano turistico.

Se evalua en 3 ESCENARIOS (pesimista / base / optimista) que mueven a la vez
la ocupacion turistica y sus costes, porque son justo las variables sin dato
local y de las que depende toda la conclusion.

ROI se reporta sobre DOS denominadores:
  - precio de compra (237.950 €)
  - inversion total = precio de compra + gastos de adquisicion (~264.000 €)
La segunda es la que refleja el dinero realmente desembolsado.
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

# ===========================================================================
# BLOQUE 2 — SUPUESTOS (esto NO son datos observados)
# ===========================================================================
# Calendario (compartido con serie_temporal_estrategias.py para que los dos
# modelos no se contradigan)
MESES_ACADEMICOS = {9, 10, 11, 12, 1, 2, 3, 4, 5, 6}   # sep-jun
N_MESES_CURSO = len(MESES_ACADEMICOS)                   # 10
N_MESES_VERANO = 12 - N_MESES_CURSO                     # 2 (jul-ago)

# Gastos comunes a cualquier estrategia
COMUNIDAD_MES = 70.0
IBI_PCT_CATASTRAL = 0.00767          # dato oficial del municipio (tipo urbano)
RATIO_CATASTRAL_MERCADO = 0.55       # SUPUESTO: valor catastral ~50-60% del de mercado
ITP_MAS_GASTOS_COMPRA_PCT = 0.11     # SUPUESTO: punto medio del 10-12%

# Residencial / estudiantil
SEGURO_IMPAGO_PCT = 0.065            # SUPUESTO: punto medio del rango 5-8%
OCUPACION_RESIDENCIAL = 0.95         # SUPUESTO: rotacion de inquilinos
OCUPACION_ESTUDIANTIL_CURSO = 0.95   # SUPUESTO
OCUPACION_ESTUDIANTIL_VERANO = 0.30  # SUPUESTO: la demanda universitaria desaparece

# Fiscalidad
REDUCCION_IRPF_RESIDENCIAL = 0.50    # caso general, contratos posteriores a mayo 2023
REDUCCION_IRPF_TURISTICO = 0.0       # sin reduccion (capital inmobiliario puro)

# --- Escenarios turisticos: ocupacion Y costes se mueven juntos -------------
# Ninguna de estas cifras es un dato de San Vicente del Raspeig. La ocupacion
# base (77%) es un proxy de Alicante ciudad; los costes operativos son
# estimaciones de mercado, no presupuestos pedidos a proveedores locales.
ESCENARIOS = {
    "pesimista": dict(
        ocupacion=0.45,
        comision_pct=0.15,          # todo via Booking (~15%)
        gestion_pct=0.18,           # gestion integral externalizada
        limpieza_por_estancia=60.0,
        noches_por_estancia=3.0,    # estancias cortas -> mas limpiezas
        suministros_mes=150.0,      # aire acondicionado en verano, todo a cargo del propietario
        mantenimiento_pct=0.07,     # reposicion textil/menaje, mayor desgaste
    ),
    "base": dict(
        ocupacion=0.60,
        comision_pct=0.12,          # mezcla Airbnb split-fee / Booking
        gestion_pct=0.10,           # gestion parcial
        limpieza_por_estancia=50.0,
        noches_por_estancia=4.0,
        suministros_mes=120.0,
        mantenimiento_pct=0.05,
    ),
    "optimista": dict(
        ocupacion=0.77,             # el proxy de Alicante ciudad pasa a ser el TECHO, no el caso base
        comision_pct=0.05,          # casi todo Airbnb con split-fee (~3%)
        gestion_pct=0.0,            # autogestion (coste en tiempo propio, no en dinero)
        limpieza_por_estancia=45.0,
        noches_por_estancia=5.0,    # estancias largas -> menos limpiezas
        suministros_mes=100.0,
        mantenimiento_pct=0.04,
    ),
}

SUPUESTOS_DOC = [
    ("comunidad_mes", COMUNIDAD_MES, "EUR/mes", "todas",
     "Punto medio del rango 40-100 EUR/mes para piso estandar sin extras"),
    ("ibi_pct_catastral", IBI_PCT_CATASTRAL, "% s/ valor catastral", "todas",
     "DATO OFICIAL del municipio (tipo urbano). Lo que es supuesto es el valor catastral, no el tipo"),
    ("ratio_catastral_mercado", RATIO_CATASTRAL_MERCADO, "ratio", "todas",
     "SUPUESTO: el valor catastral suele rondar el 50-60% del de mercado. No es el valor catastral real de una vivienda concreta"),
    ("itp_mas_gastos_compra_pct", ITP_MAS_GASTOS_COMPRA_PCT, "% s/ precio compra", "todas",
     "Punto medio del 10-12% (ITP 9% CV + notaria + registro + gestoria)"),
    ("seguro_impago_pct", SEGURO_IMPAGO_PCT, "% s/ renta bruta", "residencial/estudiantil",
     "Punto medio del rango 5-8% de la renta anual bruta"),
    ("ocupacion_residencial", OCUPACION_RESIDENCIAL, "ratio", "residencial",
     "SUPUESTO: vacancia por rotacion de inquilinos. Sin dato local de rotacion"),
    ("ocupacion_estudiantil_curso", OCUPACION_ESTUDIANTIL_CURSO, "ratio", "estudiantil/mixto",
     "SUPUESTO: habitaciones casi siempre ocupadas durante el curso"),
    ("ocupacion_estudiantil_verano", OCUPACION_ESTUDIANTIL_VERANO, "ratio", "estudiantil",
     "SUPUESTO: la demanda universitaria desaparece en jul-ago. Sin serie historica de la UA"),
    ("meses_curso", N_MESES_CURSO, "meses", "estudiantil/mixto",
     "Calendario academico sep-jun"),
    ("reduccion_irpf_residencial", REDUCCION_IRPF_RESIDENCIAL, "ratio", "residencial/estudiantil",
     "Normativa: reduccion general del 50% del rendimiento neto (contratos post mayo 2023)"),
    ("reduccion_irpf_turistico", REDUCCION_IRPF_TURISTICO, "ratio", "turistico",
     "Normativa: el vacacional sin servicios de hosteleria no tiene reduccion"),
]


def documentar_supuestos():
    """Exporta los supuestos a CSV para que en Power BI se puedan mostrar
    separados de los datos observados (y para que se vea que NINGUNO es una
    medicion local)."""
    filas = [dict(clave=c, valor=v, unidad=u, ambito=a, justificacion=j, tipo="SUPUESTO")
             for c, v, u, a, j in SUPUESTOS_DOC]
    for nombre, esc in ESCENARIOS.items():
        for clave, valor in esc.items():
            filas.append(dict(clave=f"{clave}", valor=valor, unidad="", ambito=f"turistico [escenario {nombre}]",
                              justificacion="Escenario turistico: ninguna de estas cifras es un dato de San Vicente",
                              tipo="SUPUESTO"))
    return pd.DataFrame(filas)


# ===========================================================================
# BLOQUE 1 — DATOS OBSERVADOS (de los CSV limpios, con su n)
# ===========================================================================
def cargar_arquetipo(verbose=True):
    alq = pd.read_csv(LIMPIO_DIR / "alquiler_residencial_limpio.csv", sep=";")
    venta = pd.read_csv(LIMPIO_DIR / "venta_limpio.csv", sep=";")
    ua = pd.read_csv(LIMPIO_DIR / "ua_limpio.csv", sep=";")
    ua = ua[~ua["es_duplicado"]]
    turistico = pd.read_csv(LIMPIO_DIR / "turistico_precios_limpio.csv", sep=";")

    arquetipo_alq = alq[(alq["habitaciones"] == 3) & (alq["m2"].between(70, 130)) &
                         (alq["tipo_alquiler"] == "anual/no_especificado")]
    arquetipo_venta = venta[(venta["habitaciones"] == 3) & (venta["m2"].between(70, 130)) &
                             (~venta["es_outlier_lujo"])]
    ua_hab = ua[ua["tipo_oferta_simplificado"] == "habitacion"]["precio_num"]
    tur_completa = turistico[turistico["categoria"] == "vivienda_completa"]["precio_noche"]

    datos = {
        "precio_compra": arquetipo_venta["precio"].median(),
        "n_compra": len(arquetipo_venta),
        "precio_residencial_mes": arquetipo_alq["precio_mes"].median(),
        "n_residencial": len(arquetipo_alq),
        "precio_habitacion_mes": ua_hab.median(),
        "n_habitacion": int(ua_hab.count()),
        "precio_noche_turistico": tur_completa.median(),
        "n_turistico": int(tur_completa.count()),
    }

    if verbose:
        print("=" * 78)
        print("BLOQUE 1 — DATOS OBSERVADOS (de los CSV limpios del proyecto)")
        print("=" * 78)
        print(f"Precio de compra ................ {datos['precio_compra']:>10,.0f} EUR/vivienda   (mediana, n={datos['n_compra']})")
        print(f"Alquiler residencial ............ {datos['precio_residencial_mes']:>10,.0f} EUR/mes        (mediana, n={datos['n_residencial']})")
        print(f"Alquiler por habitacion (UA) .... {datos['precio_habitacion_mes']:>10,.0f} EUR/hab./mes   (mediana, n={datos['n_habitacion']})")
        print(f"Precio/noche turistico .......... {datos['precio_noche_turistico']:>10,.0f} EUR/noche      (mediana, n={datos['n_turistico']})  <-- n pequeño, menos robusto")
        print()
        print("=" * 78)
        print("BLOQUE 2 — SUPUESTOS (hipotesis del modelo, NO datos de San Vicente)")
        print("=" * 78)
        print("Ocupaciones, comisiones, limpieza, suministros, gestion, IBI estimado,")
        print("gastos de compra y reducciones de IRPF -> ver eda/supuestos_modelo.csv")
        print()

    return datos


def datos_observados_df(datos):
    return pd.DataFrame([
        dict(concepto="Precio de compra (arquetipo 3 hab.)", valor=datos["precio_compra"],
             unidad="EUR", n=datos["n_compra"], fuente="limpio/venta_limpio.csv", tipo="DATO OBSERVADO"),
        dict(concepto="Alquiler residencial anual", valor=datos["precio_residencial_mes"],
             unidad="EUR/mes", n=datos["n_residencial"], fuente="limpio/alquiler_residencial_limpio.csv", tipo="DATO OBSERVADO"),
        dict(concepto="Alquiler por habitacion (UA)", valor=datos["precio_habitacion_mes"],
             unidad="EUR/hab./mes", n=datos["n_habitacion"], fuente="limpio/ua_limpio.csv", tipo="DATO OBSERVADO"),
        dict(concepto="Precio/noche turistico (vivienda completa)", valor=datos["precio_noche_turistico"],
             unidad="EUR/noche", n=datos["n_turistico"], fuente="limpio/turistico_precios_limpio.csv", tipo="DATO OBSERVADO"),
    ])


# ===========================================================================
# Motor de calculo
# ===========================================================================
def gastos_fijos_anuales(precio_compra):
    ibi = precio_compra * RATIO_CATASTRAL_MERCADO * IBI_PCT_CATASTRAL
    comunidad = COMUNIDAD_MES * 12
    return ibi, comunidad


def bruto_turistico_anual(datos, ocupacion, meses=12):
    return datos["precio_noche_turistico"] * 30.4 * ocupacion * meses


def gastos_operativos_turistico(datos, esc, ocupacion, meses=12):
    """
    Costes que el modelo anterior NO tenia y que son propios del vacacional:
      - limpieza entre estancias (depende de cuantas estancias hay: a mas
        rotacion, mas limpiezas)
      - suministros: en vacacional los paga el propietario, no el inquilino
      - mantenimiento/reposicion: textiles, menaje, mayor desgaste
      - gestion: si no la lleva el propietario
      - comision de plataforma
    """
    bruto = bruto_turistico_anual(datos, ocupacion, meses)
    noches_ocupadas = 30.4 * ocupacion * meses
    n_estancias = noches_ocupadas / esc["noches_por_estancia"]

    limpieza = n_estancias * esc["limpieza_por_estancia"]
    suministros = esc["suministros_mes"] * meses
    mantenimiento = bruto * esc["mantenimiento_pct"]
    gestion = bruto * esc["gestion_pct"]
    comision = bruto * esc["comision_pct"]

    total = limpieza + suministros + mantenimiento + gestion + comision
    detalle = dict(limpieza=limpieza, suministros=suministros, mantenimiento=mantenimiento,
                   gestion=gestion, comision=comision)
    return total, detalle


def calcular_estrategias(datos, nombre_escenario):
    esc = ESCENARIOS[nombre_escenario]
    precio_compra = datos["precio_compra"]
    inversion_total = precio_compra * (1 + ITP_MAS_GASTOS_COMPRA_PCT)
    ibi, comunidad = gastos_fijos_anuales(precio_compra)
    gastos_fijos = ibi + comunidad

    filas = []

    # --- 1. Residencial anual ---
    bruto = datos["precio_residencial_mes"] * 12 * OCUPACION_RESIDENCIAL
    gastos = gastos_fijos + bruto * SEGURO_IMPAGO_PCT
    neto = bruto - gastos
    filas.append(dict(escenario=nombre_escenario, estrategia="1. Residencial anual",
                      ingreso_bruto=bruto, gastos=gastos, ingreso_neto=neto,
                      base_imponible_irpf=neto * (1 - REDUCCION_IRPF_RESIDENCIAL)))

    # --- 2. Estudiantil por habitacion (curso + verano por separado) ---
    bruto_curso = datos["precio_habitacion_mes"] * 3 * N_MESES_CURSO * OCUPACION_ESTUDIANTIL_CURSO
    bruto_verano = datos["precio_habitacion_mes"] * 3 * N_MESES_VERANO * OCUPACION_ESTUDIANTIL_VERANO
    bruto = bruto_curso + bruto_verano
    gastos = gastos_fijos + bruto * SEGURO_IMPAGO_PCT
    neto = bruto - gastos
    filas.append(dict(escenario=nombre_escenario, estrategia="2. Estudiantil x habitacion",
                      ingreso_bruto=bruto, gastos=gastos, ingreso_neto=neto,
                      base_imponible_irpf=neto * (1 - REDUCCION_IRPF_RESIDENCIAL)))

    # --- 3. Turistico (con costes operativos completos) ---
    bruto = bruto_turistico_anual(datos, esc["ocupacion"], 12)
    op, _ = gastos_operativos_turistico(datos, esc, esc["ocupacion"], 12)
    gastos = gastos_fijos + op
    neto = bruto - gastos
    filas.append(dict(escenario=nombre_escenario, estrategia="3. Turistico (Airbnb/Booking)",
                      ingreso_bruto=bruto, gastos=gastos, ingreso_neto=neto,
                      base_imponible_irpf=neto * (1 - REDUCCION_IRPF_TURISTICO)))

    # --- 4. Mixto: curso por habitaciones + verano turistico ---
    bruto_curso = datos["precio_habitacion_mes"] * 3 * N_MESES_CURSO * OCUPACION_ESTUDIANTIL_CURSO
    bruto_verano = bruto_turistico_anual(datos, esc["ocupacion"], N_MESES_VERANO)
    bruto = bruto_curso + bruto_verano
    op_verano, _ = gastos_operativos_turistico(datos, esc, esc["ocupacion"], N_MESES_VERANO)
    gastos = gastos_fijos + bruto_curso * SEGURO_IMPAGO_PCT + op_verano
    neto = bruto - gastos
    base_irpf = (neto * (bruto_curso / bruto)) * (1 - REDUCCION_IRPF_RESIDENCIAL) + \
                (neto * (bruto_verano / bruto)) * (1 - REDUCCION_IRPF_TURISTICO)
    filas.append(dict(escenario=nombre_escenario, estrategia="4. Mixto (curso+verano turistico)",
                      ingreso_bruto=bruto, gastos=gastos, ingreso_neto=neto,
                      base_imponible_irpf=base_irpf))

    df = pd.DataFrame(filas)
    df["ingreso_neto_mes"] = df["ingreso_neto"] / 12
    df["yield_bruto_s_compra"] = df["ingreso_bruto"] / precio_compra
    df["roi_neto_s_compra"] = df["ingreso_neto"] / precio_compra
    df["roi_neto_s_inversion_total"] = df["ingreso_neto"] / inversion_total
    df["payback_anos_s_inversion_total"] = inversion_total / df["ingreso_neto"]
    return df


def ocupacion_break_even(datos, nombre_escenario, roi_objetivo_eur):
    """Ocupacion turistica a la que el NETO del turistico iguala un neto dado
    (p.ej. el del residencial). Los costes operativos hacen que la relacion ya
    no sea perfectamente lineal (la limpieza escala con las noches ocupadas),
    asi que se resuelve por barrido fino en vez de por interpolacion."""
    esc = ESCENARIOS[nombre_escenario]
    precio_compra = datos["precio_compra"]
    ibi, comunidad = gastos_fijos_anuales(precio_compra)
    gastos_fijos = ibi + comunidad

    anterior = None
    for i in range(1, 991):
        oc = i / 1000
        bruto = bruto_turistico_anual(datos, oc, 12)
        op, _ = gastos_operativos_turistico(datos, esc, oc, 12)
        neto = bruto - gastos_fijos - op
        if anterior is not None and anterior < roi_objetivo_eur <= neto:
            return oc
        anterior = neto
    return None


def main():
    os.makedirs(EDA_DIR, exist_ok=True)
    datos = cargar_arquetipo()

    precio_compra = datos["precio_compra"]
    inversion_total = precio_compra * (1 + ITP_MAS_GASTOS_COMPRA_PCT)
    ibi, comunidad = gastos_fijos_anuales(precio_compra)

    print(f"Inversion total desembolsada: {inversion_total:,.0f} EUR "
          f"(compra {precio_compra:,.0f} + gastos de adquisicion {inversion_total - precio_compra:,.0f})")
    print(f"Gastos fijos anuales: {ibi + comunidad:,.0f} EUR (IBI estimado {ibi:,.0f} + comunidad {comunidad:,.0f})")
    print()

    todos = pd.concat([calcular_estrategias(datos, nombre) for nombre in ESCENARIOS], ignore_index=True)

    for nombre in ESCENARIOS:
        esc = ESCENARIOS[nombre]
        sub = todos[todos["escenario"] == nombre]
        print("-" * 78)
        print(f"ESCENARIO {nombre.upper()}  (ocupacion turistica {esc['ocupacion']:.0%}, "
              f"comision {esc['comision_pct']:.0%}, gestion {esc['gestion_pct']:.0%}, "
              f"limpieza {esc['limpieza_por_estancia']:.0f}EUR/{esc['noches_por_estancia']:.0f}noches)")
        print("-" * 78)
        tabla = sub[["estrategia", "ingreso_bruto", "gastos", "ingreso_neto", "ingreso_neto_mes",
                     "roi_neto_s_compra", "roi_neto_s_inversion_total", "payback_anos_s_inversion_total"]].copy()
        for c in ["ingreso_bruto", "gastos", "ingreso_neto", "ingreso_neto_mes"]:
            tabla[c] = tabla[c].round(0)
        for c in ["roi_neto_s_compra", "roi_neto_s_inversion_total"]:
            tabla[c] = (tabla[c] * 100).round(2)
        tabla["payback_anos_s_inversion_total"] = tabla["payback_anos_s_inversion_total"].round(1)
        print(tabla.to_string(index=False))
        ganador = sub.loc[sub["ingreso_neto"].idxmax()]
        print(f"  -> Mejor en este escenario: {ganador['estrategia']} "
              f"({ganador['roi_neto_s_inversion_total']*100:.2f}% ROI neto sobre inversion total)")
        print()

    # --- desglose de costes turisticos (lo que faltaba en el modelo anterior) ---
    print("=" * 78)
    print("DESGLOSE DE COSTES OPERATIVOS DEL TURISTICO (lo que el modelo anterior no contaba)")
    print("=" * 78)
    filas_costes = []
    for nombre, esc in ESCENARIOS.items():
        bruto = bruto_turistico_anual(datos, esc["ocupacion"], 12)
        _, det = gastos_operativos_turistico(datos, esc, esc["ocupacion"], 12)
        fila = dict(escenario=nombre, ingreso_bruto=round(bruto))
        fila.update({k: round(v) for k, v in det.items()})
        fila["total_operativo"] = round(sum(det.values()))
        fila["pct_sobre_bruto"] = round(sum(det.values()) / bruto * 100, 1)
        filas_costes.append(fila)
    costes_df = pd.DataFrame(filas_costes)
    print(costes_df.to_string(index=False))
    print()

    # --- conclusion CONDICIONAL ---
    print("=" * 78)
    print("CONCLUSION (condicional, como debe ser)")
    print("=" * 78)
    for nombre in ESCENARIOS:
        sub = todos[todos["escenario"] == nombre]
        neto_resid = sub[sub["estrategia"] == "1. Residencial anual"]["ingreso_neto"].iloc[0]
        be = ocupacion_break_even(datos, nombre, neto_resid)
        esc = ESCENARIOS[nombre]
        if be:
            print(f"  [{nombre}] con esa estructura de costes, el turistico supera al residencial "
                  f"a partir del {be:.1%} de ocupacion (el escenario asume {esc['ocupacion']:.0%}).")
        else:
            print(f"  [{nombre}] el turistico no alcanza al residencial en ningun nivel de ocupacion realista.")
    print()
    print("  Redaccion recomendada para la memoria:")
    print("  \"El alquiler turistico maximiza la rentabilidad bajo escenarios de ocupacion")
    print("   superiores a los umbrales indicados, mientras que el residencial ofrece menor")
    print("   rentabilidad potencial pero mucha menor exposicion a la estacionalidad y a los")
    print("   costes operativos. La ocupacion turistica real de San Vicente del Raspeig no")
    print("   esta medida en este trabajo: es el supuesto del que depende la conclusion.\"")

    # --- exportaciones para Power BI ---
    todos.to_csv(EDA_DIR / "comparativa_estrategias_escenarios.csv", sep=";", index=False)
    costes_df.to_csv(EDA_DIR / "costes_turistico_desglose.csv", sep=";", index=False)
    documentar_supuestos().to_csv(EDA_DIR / "supuestos_modelo.csv", sep=";", index=False)
    datos_observados_df(datos).to_csv(EDA_DIR / "datos_observados.csv", sep=";", index=False)

    # compatibilidad: el escenario base se sigue exportando con el nombre de siempre
    base = todos[todos["escenario"] == "base"].copy()
    base.to_csv(EDA_DIR / "comparativa_estrategias.csv", sep=";", index=False)

    print(f"\nExportado a {EDA_DIR}:")
    print("  comparativa_estrategias_escenarios.csv (3 escenarios x 4 estrategias)")
    print("  costes_turistico_desglose.csv | supuestos_modelo.csv | datos_observados.csv")

    graficar_escenarios(todos)


def graficar_escenarios(todos):
    os.makedirs(GRAF_DIR, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 5))
    estrategias = todos["estrategia"].unique()
    escenarios = list(ESCENARIOS.keys())
    ancho = 0.25
    colores = {"pesimista": "#a53b3b", "base": "#3b6ea5", "optimista": "#3ba55d"}

    for i, esc in enumerate(escenarios):
        sub = todos[todos["escenario"] == esc].set_index("estrategia").loc[estrategias]
        pos = [j + (i - 1) * ancho for j in range(len(estrategias))]
        ax.bar(pos, sub["roi_neto_s_inversion_total"] * 100, ancho, label=esc, color=colores[esc])

    ax.set_xticks(range(len(estrategias)))
    ax.set_xticklabels([e.split(". ")[1] for e in estrategias], rotation=15, ha="right")
    ax.set_ylabel("ROI neto anual (%) sobre inversion total")
    ax.set_title("ROI por estrategia y escenario turistico\n"
                 "(la ocupacion y los costes operativos del turistico son SUPUESTOS, no datos locales)")
    ax.legend(title="escenario")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    out = GRAF_DIR / "09_escenarios_roi.png"
    fig.savefig(out)
    plt.close(fig)
    print(f"Grafico guardado en: {out}")


if __name__ == "__main__":
    main()

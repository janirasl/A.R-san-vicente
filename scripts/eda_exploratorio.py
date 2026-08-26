"""
EDA exploratorio sobre los 5 CSV limpios (alquiler_residencial, venta, ua, vut,
turistico). Objetivo: entender distribuciones de precio y precio/m2 por
tipo_oferta, y dejar listo el terreno para el modelo financiero comparativo
(modelo_financiero.py), que es donde se responde la pregunta real del
proyecto (que estrategia maximiza ROI).

Genera graficos en ../graficos/ y un resumen por consola.
"""

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
LIMPIO_DIR = SCRIPT_DIR.parent / "limpio"
GRAF_DIR = SCRIPT_DIR.parent / "graficos"

plt.rcParams["figure.dpi"] = 110
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3


def marcar_m2_sospechosos(df, m2_col="m2", precio_col="precio_mes", min_eur_m2=3.0):
    """
    Deteccion de calidad de datos encontrada durante el EDA: unas pocas filas
    de alquiler_residencial_limpio tienen un m2 claramente erroneo (382 m2 o
    900 m2 para un piso de 3-4 hab a 900-930 eur/mes -> saldria a 1-2 eur/m2,
    muy por debajo de cualquier alquiler real). Es un fallo de la fuente RAW
    (no de la limpieza), asi que aqui NO se borran filas: se marca
    'm2_sospechoso' para poder excluirlas de los calculos de precio/m2 sin
    perder el registro (misma filosofia que es_duplicado_cruzado /
    es_outlier_lujo en los otros scripts de limpieza).
    """
    df = df.copy()
    precio_m2 = df[precio_col] / df[m2_col]
    df["m2_sospechoso"] = precio_m2 < min_eur_m2
    return df


def eda_alquiler_residencial():
    df = pd.read_csv(LIMPIO_DIR / "alquiler_residencial_limpio.csv", sep=";")
    df = marcar_m2_sospechosos(df)
    n_sosp = df["m2_sospechoso"].sum()
    print(f"[alquiler_residencial] {len(df)} viviendas | {n_sosp} con m2 sospechoso (excluidas de precio/m2)")

    valido = df[~df["m2_sospechoso"]].dropna(subset=["m2"])
    valido = valido.copy()
    valido["precio_m2"] = valido["precio_mes"] / valido["m2"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].hist(df["precio_mes"].dropna(), bins=20, color="#3b6ea5", edgecolor="white")
    axes[0].set_title("Alquiler residencial: distribucion de precio/mes")
    axes[0].set_xlabel("EUR/mes")
    axes[0].set_ylabel("nº viviendas")

    data_por_hab = [valido[valido["habitaciones"] == h]["precio_m2"].dropna()
                     for h in sorted(valido["habitaciones"].unique()) if (valido["habitaciones"] == h).sum() >= 3]
    labels_hab = [str(h) for h in sorted(valido["habitaciones"].unique()) if (valido["habitaciones"] == h).sum() >= 3]
    axes[1].boxplot(data_por_hab, tick_labels=labels_hab)
    axes[1].set_title("Precio/m2 por nº de habitaciones")
    axes[1].set_xlabel("habitaciones")
    axes[1].set_ylabel("EUR/m2/mes")

    fig.tight_layout()
    fig.savefig(GRAF_DIR / "01_alquiler_residencial_precio.png")
    plt.close(fig)

    print(f"  Precio/m2 medio (excl. sospechosos): {valido['precio_m2'].mean():.2f} EUR/m2/mes "
          f"(mediana {valido['precio_m2'].median():.2f})")
    print(f"  Comparativa por fuente:\n{df.groupby('fuente')['precio_mes'].agg(['count', 'mean', 'median']).round(1)}")
    return df


def eda_venta():
    df = pd.read_csv(LIMPIO_DIR / "venta_limpio.csv", sep=";")
    print(f"\n[venta] {len(df)} viviendas | {df['es_outlier_lujo'].sum()} outliers de lujo (p95)")

    sin_lujo = df[~df["es_outlier_lujo"]]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].hist(sin_lujo["precio_m2"].dropna(), bins=20, color="#a53b3b", edgecolor="white")
    axes[0].set_title("Venta: distribucion precio/m2 (sin outliers de lujo)")
    axes[0].set_xlabel("EUR/m2")

    por_tipo = sin_lujo.groupby("tipo_vivienda")["precio_m2"].mean().sort_values()
    axes[1].barh(por_tipo.index, por_tipo.values, color="#a53b3b")
    axes[1].set_title("Precio/m2 medio por tipo de vivienda")
    axes[1].set_xlabel("EUR/m2")

    fig.tight_layout()
    fig.savefig(GRAF_DIR / "02_venta_precio.png")
    plt.close(fig)

    print(f"  Precio/m2 medio sin outliers de lujo: {sin_lujo['precio_m2'].mean():.0f} EUR/m2")
    print(f"  Por tipo de vivienda:\n{por_tipo.round(0)}")
    return df


def eda_ua():
    df = pd.read_csv(LIMPIO_DIR / "ua_limpio.csv", sep=";")
    df = df[~df["es_duplicado"]]
    print(f"\n[UA bolsa alojamiento] {len(df)} ofertas (sin duplicados internos)")
    print(df["tipo_oferta_simplificado"].value_counts())

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    grupos = [df[df["tipo_oferta_simplificado"] == "habitacion"]["precio_num"].dropna(),
              df[df["tipo_oferta_simplificado"] == "piso_completo"]["precio_num"].dropna()]
    ax.boxplot(grupos, tick_labels=["habitacion", "piso_completo"])
    ax.set_title("UA Bolsa de Alojamiento: precio por tipo de oferta")
    ax.set_ylabel("EUR/mes")
    fig.tight_layout()
    fig.savefig(GRAF_DIR / "03_ua_precio.png")
    plt.close(fig)

    hab = df[df["tipo_oferta_simplificado"] == "habitacion"]["precio_num"]
    piso = df[df["tipo_oferta_simplificado"] == "piso_completo"]["precio_num"]
    print(f"  Habitacion: media {hab.mean():.0f} / mediana {hab.median():.0f} EUR/mes (n={hab.count()})")
    print(f"  Piso completo: media {piso.mean():.0f} / mediana {piso.median():.0f} EUR/mes (n={piso.count()})")
    return df


def eda_turistico():
    df = pd.read_csv(LIMPIO_DIR / "turistico_precios_limpio.csv", sep=";")
    print(f"\n[turistico Airbnb+Booking] {len(df)} anuncios en San Vicente | "
          f"{df['posible_duplicado_cruzado'].sum()} posibles duplicados cruzados (marcados, no borrados)")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    por_cat = df.groupby("categoria")["precio_noche"].median().sort_values()
    ax.barh(por_cat.index, por_cat.values, color="#3ba55d")
    ax.set_title("Turistico: precio/noche mediano por categoria")
    ax.set_xlabel("EUR/noche")
    fig.tight_layout()
    fig.savefig(GRAF_DIR / "04_turistico_precio.png")
    plt.close(fig)

    print(df.groupby("categoria")["precio_noche"].agg(["count", "mean", "median"]).round(1))
    return df


def eda_vut():
    df = pd.read_csv(LIMPIO_DIR / "vut_limpio.csv", sep=";")
    df = df[~df["es_duplicado"]]
    print(f"\n[VUT registro oficial] {len(df)} viviendas turisticas registradas (sin duplicados internos)")
    print(f"  Superficie media: {df['superficie_m2'].mean():.0f} m2 | Dormitorios medios: {df['dormitorios'].mean():.1f}")
    return df


def eda_comparativa_bruta(alq, ua, turistico):
    """
    Primera foto comparativa (solo ingreso BRUTO mensual, sin gastos todavia)
    para el arquetipo de piso de 3 habitaciones / ~90-100 m2, que es el mas
    representativo tanto en alquiler (66/144 = 46%) como en venta (31/99) y
    en UA piso completo (10/17). El modelo con gastos/ROI real esta en
    modelo_financiero.py -- este grafico es solo para visualizar de un
    vistazo por que hace falta ese siguiente paso (el bruto por si solo
    engana: turistico parece ganador, pero tiene mas gastos y peor fiscalidad).
    """
    arquetipo_alq = alq[(alq["habitaciones"] == 3) & (alq["m2"].between(70, 130)) &
                         (alq["tipo_alquiler"] == "anual/no_especificado")]
    precio_residencial = arquetipo_alq["precio_mes"].median()

    precio_habitacion = ua[ua["tipo_oferta_simplificado"] == "habitacion"]["precio_num"].median()
    precio_estudiantil_3hab = precio_habitacion * 3

    viv_completa = turistico[turistico["categoria"] == "vivienda_completa"]["precio_noche"].median()
    ocupacion_asumida = 0.77  # proxy Alicante, ver notas de supuestos
    precio_turistico_mes = viv_completa * 30.4 * ocupacion_asumida

    valores = {
        "Residencial anual\n(piso completo)": precio_residencial,
        f"Estudiantil x hab.\n(3 hab. x {precio_habitacion:.0f}€)": precio_estudiantil_3hab,
        f"Turistico\n(ocupacion {ocupacion_asumida:.0%})": precio_turistico_mes,
    }

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(valores.keys(), valores.values(), color=["#3b6ea5", "#e0a020", "#3ba55d"])
    ax.set_title("Ingreso BRUTO mensual por estrategia — arquetipo 3 hab. / ~90-100 m2\n(sin gastos ni fiscalidad, ver modelo_financiero.py)")
    ax.set_ylabel("EUR/mes")
    for i, (k, v) in enumerate(valores.items()):
        ax.text(i, v + 15, f"{v:.0f}€", ha="center")
    fig.tight_layout()
    fig.savefig(GRAF_DIR / "05_comparativa_bruta_arquetipo.png")
    plt.close(fig)

    print("\n[Comparativa BRUTA, arquetipo 3 hab. / ~90-100 m2 — SOLO ingreso, sin gastos]")
    for k, v in valores.items():
        print(f"  {k.replace(chr(10), ' ')}: {v:.0f} EUR/mes")
    print("  -> Esta comparativa es enganosa por si sola: el turistico bruto es el mas alto,")
    print("     pero es el que mas gastos/comision tiene y el unico sin reduccion fiscal IRPF.")
    print("     El ranking real esta en modelo_financiero.py (ingreso NETO y ROI).")


def main():
    os.makedirs(GRAF_DIR, exist_ok=True)
    alq = eda_alquiler_residencial()
    eda_venta()
    ua = eda_ua()
    turistico = eda_turistico()
    eda_vut()
    eda_comparativa_bruta(alq, ua, turistico)
    print(f"\nGraficos guardados en: {GRAF_DIR}")


if __name__ == "__main__":
    main()

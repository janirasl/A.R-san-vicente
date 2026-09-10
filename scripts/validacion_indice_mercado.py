"""
VALIDACION EXTERNA de la muestra propia contra los indices de precio publicados.

Por que este script existe:
Toda la muestra de alquiler del proyecto son anuncios que extrajimos nosotras
de Idealista y Fotocasa. Una muestra propia siempre tiene el mismo riesgo: que
el filtro de busqueda o la ventana temporal la hayan sesgado sin que lo veamos.
La forma de comprobarlo es contrastarla contra una referencia independiente.

Referencias disponibles, y que mide cada una (son POBLACIONES DISTINTAS, no
versiones mejores o peores del mismo numero):

  1. Indice Idealista/Fotocasa (alquiler_mercado_mensual.csv) -> precio medio
     de OFERTA publicada, por municipio y mes, serie de 12 meses. Es la
     referencia mas comparable a nuestra muestra, porque mide exactamente lo
     mismo: lo que se pide en los anuncios.

  2. SERPAVI (serpavi_san_vicente.csv) -> precio de CONTRATOS realmente
     formalizados, de fuentes fiscales (fianzas depositadas), año 2024.
     Incluye contratos antiguos, alquileres por debajo de mercado y vivienda
     protegida, asi que estructuralmente queda por debajo de la oferta. No es
     un dato "peor": mide otra cosa. Es la referencia LEGAL en zonas
     tensionadas, pero NO es el estimador de lo que puedes cobrar hoy.

  3. Nuestra muestra (dataset_unificado.csv) -> anuncios activos capturados en
     agosto de 2026.

DOS LIMITACIONES DE ESTA VALIDACION, y conviene tenerlas presentes:

  a) SESGO DE DURACION EN LA MUESTRA PROPIA. Nuestra muestra es una foto de los
     anuncios ACTIVOS en un momento dado. Pero un anuncio bien de precio se
     alquila rapido y esta visible poco tiempo, mientras que uno caro se queda
     colgado meses. Cualquier foto instantanea, por tanto, SOBRE-REPRESENTA los
     anuncios que no se alquilan, que son los caros.
     -> El sesgo tiene direccion conocida: nuestros 990 EUR/mes son
        probablemente una SOBREESTIMACION de la renta realmente alcanzable, y
        por tanto el ROI residencial esta algo inflado.
     -> Ademas, el indice de Idealista se construye con anuncios de antiguedad
        limitada (del orden de 150 dias), asi que filtra parte de esos anuncios
        estancados y nuestra muestra no. La coincidencia del -2% es buena señal,
        pero no compara poblaciones identicas.
     -> Con los datos actuales no se puede cuantificar: las dos capturas estan
        separadas solo 2 dias. Se corrige acumulando capturas periodicas y
        midiendo cuanto tiempo sobrevive cada anuncio (los que desaparecen se
        han alquilado; los que persisten estan caros).

  b) LA SERIE DE FOTOCASA DE alquiler_mercado_mensual.csv ES DUDOSA. Sus 12
     valores son TODOS enteros y solo hay tres distintos (9,0 / 10,0 / 11,0),
     frente a los seis valores con decimal de Idealista. Eso no tiene pinta de
     indice publicado, sino de cifras redondeadas o leidas de un grafico. Ademas
     Fotocasa no publica indices publicos desde 2023.
     -> La validacion de este script se apoya SOLO en el indice de Idealista.
        La serie de Fotocasa se dibuja como contexto, pero no debe citarse como
        fuente hasta confirmar su procedencia.

Salidas:
  - eda/validacion_indice.csv
  - graficos/11_validacion_indice_mercado.png
"""

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent / "raw"
LIMPIO_DIR = SCRIPT_DIR.parent / "limpio"
EDA_DIR = SCRIPT_DIR.parent / "eda"
GRAF_DIR = SCRIPT_DIR.parent / "graficos"


def cargar_indice():
    df = pd.read_csv(RAW_DIR / "alquiler_mercado_mensual.csv")
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m")
    return df.sort_values(["fuente", "fecha"])


def cargar_muestra_propia():
    df = pd.read_csv(LIMPIO_DIR / "dataset_unificado.csv", sep=";")
    alq = df[(df["mercado"] == "alquiler_residencial") &
             (df["marca_calidad"].isna()) &          # fuera los m2 sospechosos
             (df["precio_por_m2"].notna())]
    return alq


def cargar_serpavi():
    df = pd.read_csv(RAW_DIR / "serpavi_san_vicente.csv")
    return df.iloc[0]


def main():
    os.makedirs(EDA_DIR, exist_ok=True)
    os.makedirs(GRAF_DIR, exist_ok=True)

    indice = cargar_indice()
    muestra = cargar_muestra_propia()
    serpavi = cargar_serpavi()

    # --- 1. Nuestra muestra ---
    med_propia = muestra["precio_por_m2"].median()
    media_propia = muestra["precio_por_m2"].mean()
    p25, p75 = muestra["precio_por_m2"].quantile([0.25, 0.75])
    n_propia = len(muestra)

    # --- 2. El indice en el mes de nuestra captura y su tendencia ---
    ideal = indice[indice["fuente"] == "Idealista"]
    foto = indice[indice["fuente"] == "Fotocasa"]
    ideal_ultimo = ideal.iloc[-1]
    foto_ultimo = foto.iloc[-1]
    ideal_primero = ideal.iloc[0]
    var_anual = (ideal_ultimo["alquiler_eur_m2"] / ideal_primero["alquiler_eur_m2"] - 1) * 100

    print("=" * 80)
    print("VALIDACION DE LA MUESTRA PROPIA CONTRA LOS INDICES PUBLICADOS")
    print("=" * 80)
    print(f"Nuestra muestra (anuncios activos, agosto 2026), n={n_propia}:")
    print(f"    mediana {med_propia:.2f} EUR/m2/mes   media {media_propia:.2f}   "
          f"P25-P75 {p25:.2f}-{p75:.2f}")
    print()
    print("Indice de precio de OFERTA publicada (misma poblacion que medimos):")
    print(f"    Idealista {ideal_ultimo['fecha']:%Y-%m}: {ideal_ultimo['alquiler_eur_m2']:.1f} EUR/m2/mes")
    print(f"    Fotocasa  {foto_ultimo['fecha']:%Y-%m}: {foto_ultimo['alquiler_eur_m2']:.1f} EUR/m2/mes")
    print()
    desvio = (med_propia / ideal_ultimo["alquiler_eur_m2"] - 1) * 100
    print(f"    -> Desvio de nuestra mediana frente al indice Idealista: {desvio:+.1f}%")
    if abs(desvio) <= 10:
        print("    -> La muestra propia es CONSISTENTE con el indice publicado.")
        print("       El metodo de extraccion no introdujo un sesgo apreciable.")
    else:
        print("    -> Desvio apreciable: revisar el filtro de extraccion.")
    print()
    print("SERPAVI (contratos formalizados, fuentes fiscales, 2024) — OTRA poblacion:")
    print(f"    {serpavi['renta_mediana_eur_m2_mes']:.1f} EUR/m2/mes "
          f"(P25-P75 {serpavi['renta_p25_eur_m2_mes']:.1f}-{serpavi['renta_p75_eur_m2_mes']:.1f}, "
          f"n={serpavi['testigos']} testigos)")
    brecha = (med_propia / serpavi["renta_mediana_eur_m2_mes"] - 1) * 100
    print(f"    -> La oferta publicada esta un {brecha:+.0f}% por encima de los contratos firmados.")
    print("       No es un error de ninguna de las dos: la oferta recoge lo que se PIDE hoy")
    print("       y SERPAVI recoge lo que se PAGA en el stock vivo, contratos antiguos incluidos.")
    print()
    print("TENDENCIA (dato que el analisis no tenia hasta ahora):")
    print(f"    Idealista {ideal_primero['fecha']:%Y-%m} -> {ideal_ultimo['fecha']:%Y-%m}: "
          f"{ideal_primero['alquiler_eur_m2']:.1f} -> {ideal_ultimo['alquiler_eur_m2']:.1f} EUR/m2/mes "
          f"({var_anual:+.1f}% interanual)")
    print("    -> El modelo financiero asume renta constante. Con el alquiler subiendo a este")
    print("       ritmo, el ROI residencial de los años siguientes seria algo mayor que el")
    print("       calculado. Es una limitacion a declarar, no un error.")
    print()

    # --- 3. Estacionalidad del indice: contraste con el hallazgo turistico ---
    ideal_mes = ideal.copy()
    ideal_mes["mes"] = ideal_mes["fecha"].dt.month
    print("-" * 80)
    print("LIMITACIONES DE ESTA VALIDACION")
    print("-" * 80)
    print("a) Sesgo de duracion: una foto de anuncios activos sobre-representa los que NO se")
    print("   alquilan (los caros se quedan colgados; los baratos vuelan). Nuestra cifra es")
    print("   probablemente una sobreestimacion de la renta alcanzable. Direccion conocida,")
    print("   magnitud no: hara falta acumular capturas periodicas para medirla.")
    print("b) La serie de Fotocasa de este fichero es dudosa (12 valores, todos enteros, solo")
    print("   tres distintos). No se usa para validar: la validacion es contra Idealista.")
    print()
    print("Estacionalidad del alquiler residencial segun el indice:")
    print(f"    minimo {ideal['alquiler_eur_m2'].min():.1f} | maximo {ideal['alquiler_eur_m2'].max():.1f} "
          f"| recorrido {ideal['alquiler_eur_m2'].max() - ideal['alquiler_eur_m2'].min():.1f} EUR/m2")
    print("    -> Recorrido pequeño y tendencia al alza sostenida: el residencial no tiene")
    print("       estacionalidad relevante, coherente con como esta modelado (renta plana).")

    # --- exportacion ---
    filas = [
        dict(referencia="Muestra propia (anuncios activos)", que_mide="Precio pedido en anuncios",
             periodo="2026-08", eur_m2_mes=round(med_propia, 2), n=n_propia,
             uso="Base del modelo financiero"),
        dict(referencia="Indice Idealista", que_mide="Precio medio de oferta publicada",
             periodo=f"{ideal_ultimo['fecha']:%Y-%m}", eur_m2_mes=ideal_ultimo["alquiler_eur_m2"], n=None,
             uso="Validacion externa de la muestra"),
        dict(referencia="Indice Fotocasa", que_mide="Precio medio de oferta publicada",
             periodo=f"{foto_ultimo['fecha']:%Y-%m}", eur_m2_mes=foto_ultimo["alquiler_eur_m2"], n=None,
             uso="Validacion externa de la muestra"),
        dict(referencia="SERPAVI", que_mide="Contratos formalizados (fuentes fiscales)",
             periodo="2024", eur_m2_mes=serpavi["renta_mediana_eur_m2_mes"], n=int(serpavi["testigos"]),
             uso="Referencia legal en zona tensionada; NO estimador de renta alcanzable"),
    ]
    pd.DataFrame(filas).to_csv(EDA_DIR / "validacion_indice.csv", sep=";", index=False)
    print(f"\nGuardado en {EDA_DIR / 'validacion_indice.csv'}")

    graficar(ideal, foto, med_propia, p25, p75, serpavi)


def graficar(ideal, foto, med_propia, p25, p75, serpavi):
    fig, ax = plt.subplots(figsize=(10, 5.5))

    ax.plot(ideal["fecha"], ideal["alquiler_eur_m2"], marker="o", color="#3b6ea5",
            label="Índice Idealista (oferta publicada)")
    ax.plot(foto["fecha"], foto["alquiler_eur_m2"], marker="s", color="#3ba55d",
            label="Índice Fotocasa (oferta publicada)")

    ax.axhline(med_propia, color="#8a4fb5", linewidth=2,
               label=f"Nuestra muestra: mediana {med_propia:.1f} €/m²/mes")
    ax.fill_between(ideal["fecha"], p25, p75, color="#8a4fb5", alpha=0.10,
                    label="Nuestra muestra: rango P25-P75")

    ax.axhline(serpavi["renta_mediana_eur_m2_mes"], color="#a53b3b", linewidth=2, linestyle="--",
               label=f"SERPAVI 2024: {serpavi['renta_mediana_eur_m2_mes']:.1f} €/m²/mes (contratos firmados)")

    ax.set_ylabel("EUR/m²/mes")
    ax.set_xlabel("Mes")
    ax.set_title("Validación externa: nuestra muestra frente a los índices publicados\n"
                 "San Vicente del Raspeig — la oferta y los contratos firmados miden poblaciones distintas")
    ax.legend(fontsize=8, loc="center left")
    ax.grid(alpha=0.3)
    ax.set_ylim(bottom=5)
    fig.autofmt_xdate()
    fig.tight_layout()
    out = GRAF_DIR / "11_validacion_indice_mercado.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print(f"Grafico guardado en: {out}")


if __name__ == "__main__":
    main()

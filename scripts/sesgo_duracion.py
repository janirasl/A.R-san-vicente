"""
SESGO DE DURACION: ¿que precio tienen los anuncios que NO se alquilan?

El problema que ataca:
Nuestra muestra de alquiler es una foto de anuncios ACTIVOS. Pero un piso bien
de precio se alquila rapido y esta visible poco tiempo, mientras que uno caro se
queda colgado meses. Cualquier foto instantanea sobre-representa a los que no se
alquilan, o sea a los caros, y eso tira el precio medido hacia arriba.

Hasta ahora solo se podia declarar como limitacion, porque las dos capturas de
agosto estaban separadas por 2 dias. Con la captura del 2026-09-10 hay ya una
ventana de 15-17 dias, suficiente para que parte del stock haya rotado.

Metodo:
  1. Se toman los anuncios de Idealista del 24 y 26 de agosto.
  2. Se busca cada uno en la captura del 10 de septiembre.
  3. Los que SIGUEN -> llevan >=15 dias sin alquilarse: candidatos a estar caros.
     Los que YA NO ESTAN -> se han alquilado (o retirado).
  4. Se comparan los precios de los dos grupos.

TRES CAVEATS SERIOS, que hay que decir siempre con el resultado:

  a) El emparejamiento es HEURISTICO (precio + habitaciones + m2 +-2), porque
     las capturas de agosto no guardaron el ID del anuncio. La captura de
     septiembre SI lo guarda, asi que a partir de la siguiente el emparejamiento
     sera exacto y este analisis mucho mas fiable.

  b) Que un anuncio desaparezca NO prueba que se haya alquilado: puede haberse
     retirado, caducado o republicado con otro ID (y entonces lo contariamos mal
     como "nuevo"). El resultado es direccional, no una tasa de alquiler.

  c) 15-17 dias es una ventana corta. Un piso que tarda 3 meses en alquilarse
     sigue visible en las dos capturas y aqui aparece como "persistente" igual
     que uno que no se alquilara nunca.

Salidas:
  - eda/sesgo_duracion.csv
  - graficos/13_sesgo_duracion.png
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

TOLERANCIA_M2 = 2


def clave(df):
    """Misma clave heuristica que usa la deduplicacion del proyecto."""
    d = df.copy()
    d["m2_bin"] = (d["m2"] / TOLERANCIA_M2).round() * TOLERANCIA_M2
    return d


def main():
    os.makedirs(EDA_DIR, exist_ok=True)
    os.makedirs(GRAF_DIR, exist_ok=True)

    df = pd.read_csv(LIMPIO_DIR / "alquiler_residencial_con_marcas.csv", sep=";")
    df = df[(df["fuente"] == "idealista") & df["precio_mes"].notna() & df["m2"].notna()]
    df = clave(df)

    agosto = df[df["fecha_captura"].isin(["2026-08-24", "2026-08-26"])]
    sept = df[df["fecha_captura"] == "2026-09-10"]

    cols = ["precio_mes", "habitaciones", "m2_bin"]
    claves_sept = set(map(tuple, sept[cols].dropna().values))

    ago = agosto.drop_duplicates(subset=cols).copy()
    ago["sigue_en_septiembre"] = [tuple(v) in claves_sept for v in ago[cols].values]

    persisten = ago[ago["sigue_en_septiembre"]]
    desaparecen = ago[~ago["sigue_en_septiembre"]]

    print("=" * 84)
    print("SESGO DE DURACION — anuncios de agosto vistos de nuevo el 10 de septiembre")
    print("=" * 84)
    print(f"Ventana: 15-17 dias | Fuente: Idealista | Emparejamiento heuristico (sin ID)\n")
    print(f"Anuncios distintos en agosto ....... {len(ago)}")
    print(f"  siguen publicados en septiembre .. {len(persisten):>3}  ({len(persisten)/len(ago):.0%})")
    print(f"  ya no aparecen ................... {len(desaparecen):>3}  ({len(desaparecen)/len(ago):.0%})")
    print()

    filas = []
    for etiqueta, grupo in [("Siguen publicados (>=15 dias)", persisten),
                            ("Ya no aparecen", desaparecen)]:
        p = grupo["precio_mes"]
        pm2 = (grupo["precio_mes"] / grupo["m2"])
        print(f"{etiqueta}:")
        print(f"    precio  mediana {p.median():>7,.0f} EUR/mes   media {p.mean():>7,.0f}   n={len(grupo)}")
        print(f"    EUR/m2  mediana {pm2.median():>7.2f}          media {pm2.mean():>7.2f}")
        filas.append(dict(grupo=etiqueta, n=len(grupo),
                          precio_mediana=round(p.median()), precio_media=round(p.mean()),
                          eur_m2_mediana=round(pm2.median(), 2), eur_m2_media=round(pm2.mean(), 2)))
        print()

    dif_med = persisten["precio_mes"].median() - desaparecen["precio_mes"].median()
    dif_pct = (persisten["precio_mes"].median() / desaparecen["precio_mes"].median() - 1) * 100
    pm2_p = (persisten["precio_mes"] / persisten["m2"]).median()
    pm2_d = (desaparecen["precio_mes"] / desaparecen["m2"]).median()
    dif_m2_pct = (pm2_p / pm2_d - 1) * 100

    print("-" * 84)
    print("RESULTADO")
    print("-" * 84)
    print(f"Los que siguen colgados piden {dif_med:+,.0f} EUR/mes mas que los que desaparecieron "
          f"({dif_pct:+.1f}%).")
    print(f"En EUR/m2: {pm2_p:.2f} frente a {pm2_d:.2f} ({dif_m2_pct:+.1f}%).")
    print()
    if dif_pct > 3:
        print(">>> El sesgo de duracion QUEDA CONFIRMADO en la direccion esperada: la foto de")
        print("    anuncios activos sobre-representa los caros, porque son los que no rotan.")
        print("    Nuestra cifra de alquiler es, por tanto, una sobreestimacion de la renta")
        print("    realmente alcanzable, y el ROI residencial esta algo inflado.")
    elif dif_pct < -3:
        print(">>> Direccion CONTRARIA a la esperada. Conviene revisar el emparejamiento antes")
        print("    de sacar conclusiones.")
    else:
        print(">>> Diferencia pequeña: con esta ventana no se detecta un sesgo claro. Puede que")
        print("    15 dias sean pocos, o que el emparejamiento heuristico este diluyendo la señal.")
    print()
    print("Recordatorio de caveats: emparejamiento heuristico (no por ID), desaparecer no")
    print("equivale a alquilarse, y 15-17 dias es una ventana corta. A partir de la proxima")
    print("captura el emparejamiento sera exacto, porque desde el 10-09 se guarda el ID.")

    pd.DataFrame(filas).to_csv(EDA_DIR / "sesgo_duracion.csv", sep=";", index=False)
    print(f"\nGuardado en {EDA_DIR / 'sesgo_duracion.csv'}")

    graficar(persisten, desaparecen)


def graficar(persisten, desaparecen):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))

    datos = [desaparecen["precio_mes"].dropna(), persisten["precio_mes"].dropna()]
    axes[0].boxplot(datos, tick_labels=["Ya no aparecen\n(se alquilaron)", "Siguen colgados\n(≥15 días)"])
    axes[0].set_ylabel("EUR/mes")
    axes[0].set_title("Precio pedido según si el anuncio rotó")
    axes[0].grid(alpha=0.3)

    datos_m2 = [(desaparecen["precio_mes"] / desaparecen["m2"]).dropna(),
                (persisten["precio_mes"] / persisten["m2"]).dropna()]
    axes[1].boxplot(datos_m2, tick_labels=["Ya no aparecen", "Siguen colgados"])
    axes[1].set_ylabel("EUR/m²/mes")
    axes[1].set_title("Precio por m² según si el anuncio rotó")
    axes[1].grid(alpha=0.3)

    fig.suptitle("Sesgo de duración: los anuncios que no se alquilan son los caros\n"
                 "Idealista · San Vicente del Raspeig · ventana 24-26 ago → 10 sep",
                 fontsize=11)
    fig.tight_layout()
    out = GRAF_DIR / "13_sesgo_duracion.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print(f"Grafico guardado en: {out}")


if __name__ == "__main__":
    main()

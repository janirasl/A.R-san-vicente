"""
Limpieza del bloque turistico: VUT (registro oficial, sin precio) + Airbnb + Booking
(precios reales). Se limpian por SEPARADO porque tienen estructura distinta y
no comparten una clave fiable para cruzarlos fila a fila (Airbnb no publica
direccion, Booking da nombre del alojamiento y distancia al centro, VUT da
direccion pero no precio) -> no se puede hacer un merge automatico de verdad,
solo normalizar cada uno a precio/noche y compararlos de forma agregada.

Caso aparte: "Villa Sensation Seasons mediterránea" (Airbnb) y "Mediterranean
Seasons Sensation Villa" (Booking) son, casi con toda seguridad, el MISMO
alojamiento publicado en las dos plataformas (nombre casi identico, mismo
precio por noche ~985€, ambas en San Vicente). Se marca a mano como ejemplo,
pero un cruce sistematico por nombre haria falta si se quiere ampliar la
muestra.

Salida:
 - vut_limpio.csv         (registro, sin precio, para contar oferta y caracteristicas)
 - turistico_precios_limpio.csv (Airbnb + Booking normalizados a €/noche, solo
   listados marcados como San Vicente del Raspeig)
"""

import os
import re
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent
OUT_DIR = SCRIPT_DIR.parent / "limpio"


def parse_precio(txt):
    if pd.isna(txt) or txt == "":
        return None
    txt = str(txt).replace("€", "").strip()
    txt = txt.replace(".", "").replace(",", ".")
    try:
        return float(txt)
    except ValueError:
        return None


def clasificar_categoria_airbnb(tipo, titulo):
    t = f"{tipo} {titulo}".lower()
    if "villa" in t:
        return "villa"
    if "habitaci" in t or "hotel" in t:
        return "habitacion/hotel"
    return "vivienda_completa"


def limpiar_vut():
    df = pd.read_csv(f"{RAW_DIR}/vut_san_vicente_raspeig.csv", sep=";", dtype=str)
    df["superficie_m2"] = pd.to_numeric(df["superficie_m2"], errors="coerce")
    df["dormitorios"] = pd.to_numeric(df["dormitorios"], errors="coerce")
    df["plazas_totales"] = pd.to_numeric(df["plazas_totales"], errors="coerce")
    df["es_duplicado"] = df.duplicated(subset=["direccion", "superficie_m2", "plazas_totales"], keep="first")
    out_path = f"{OUT_DIR}/vut_limpio.csv"
    df.to_csv(out_path, sep=";", index=False)
    print(f"VUT: {len(df)} filas, {df['es_duplicado'].sum()} duplicados internos. Guardado en {out_path}")
    return df


def limpiar_airbnb():
    df = pd.read_csv(f"{RAW_DIR}/airbnb_san_vicente_raw.csv", sep=";", dtype=str)
    df = df[df["en_san_vicente"].str.strip().str.lower() == "si"].copy()
    out = pd.DataFrame(index=df.index)
    out["fuente"] = "airbnb"
    out["titulo"] = df["titulo"]
    out["categoria"] = [clasificar_categoria_airbnb(t, ti) for t, ti in zip(df["tipo"], df["titulo"])]
    out["noches"] = pd.to_numeric(df["noches"], errors="coerce")
    out["precio_total"] = df["precio_total"].apply(parse_precio)
    out["precio_noche"] = out["precio_total"] / out["noches"]
    out["valoracion"] = pd.to_numeric(df["valoracion"].str.replace(",", "."), errors="coerce")
    out["num_valoraciones"] = pd.to_numeric(df["num_valoraciones"], errors="coerce")
    return out


def limpiar_booking():
    df = pd.read_csv(f"{RAW_DIR}/booking_san_vicente_raw.csv", sep=";", dtype=str)
    df = df[df["en_san_vicente"].str.strip().str.lower() == "si"].copy()
    out = pd.DataFrame(index=df.index)
    out["fuente"] = "booking"
    out["titulo"] = df["nombre"]
    out["categoria"] = df["tipo_unidad"].apply(
        lambda t: "villa" if "villa" in str(t).lower()
        else ("habitacion/hotel" if "habitaci" in str(t).lower() else "vivienda_completa")
    )
    out["noches"] = pd.to_numeric(df["noches"], errors="coerce")
    out["precio_total"] = df["precio_total"].apply(parse_precio)
    out["precio_noche"] = out["precio_total"] / out["noches"]
    out["valoracion"] = pd.to_numeric(df["puntuacion"].str.replace(",", "."), errors="coerce")
    out["num_valoraciones"] = pd.to_numeric(df["num_comentarios"], errors="coerce")
    return out


def _palabras_relevantes(titulo):
    stopwords = {"de", "en", "la", "el", "con", "y", "a", "del", "un", "una"}
    palabras = re.findall(r"\w+", str(titulo).lower())
    return {p for p in palabras if p not in stopwords and len(p) > 3}


def marcar_posible_duplicado_por_nombre(df, umbral_palabras_comunes=2):
    """
    Heuristica de solapamiento de palabras (no exige el mismo orden ni
    ortografia identica): si dos anuncios de fuentes distintas comparten
    al menos `umbral_palabras_comunes` palabras "relevantes" en el titulo
    (p.ej. "Sensation" y "Seasons" en "Villa Sensation Seasons mediterránea"
    vs "Mediterranean Seasons Sensation Villa"), se marcan como posible
    mismo alojamiento publicado en dos plataformas. Es una heuristica de
    ayuda para revisar a mano, no una deduplicacion automatica fiable al 100%.
    """
    df = df.copy()
    sets_palabras = df["titulo"].apply(_palabras_relevantes)
    marcado = [False] * len(df)
    for i in range(len(df)):
        for j in range(i + 1, len(df)):
            if df.iloc[i]["fuente"] == df.iloc[j]["fuente"]:
                continue
            comunes = sets_palabras.iloc[i] & sets_palabras.iloc[j]
            if len(comunes) >= umbral_palabras_comunes:
                marcado[i] = True
                marcado[j] = True
    df["posible_duplicado_cruzado"] = marcado
    return df


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    limpiar_vut()

    airbnb = limpiar_airbnb()
    booking = limpiar_booking()
    combinado = pd.concat([airbnb, booking], ignore_index=True)
    combinado = marcar_posible_duplicado_por_nombre(combinado)

    out_path = f"{OUT_DIR}/turistico_precios_limpio.csv"
    combinado.to_csv(out_path, sep=";", index=False)

    print(f"\nAirbnb (San Vicente): {len(airbnb)} anuncios | Booking (San Vicente): {len(booking)} anuncios")
    print(f"Posibles duplicados cruzados por nombre: {combinado['posible_duplicado_cruzado'].sum()}")
    print("\nPrecio/noche medio por categoria (ambas fuentes juntas):")
    print(combinado.groupby("categoria")["precio_noche"].agg(["mean", "min", "max", "count"]).round(1))
    print(f"\nGuardado en: {out_path}")


if __name__ == "__main__":
    main()

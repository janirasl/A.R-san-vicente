"""
Limpieza de la Bolsa de Alojamiento UA. Se limpia sola (estructura y campos
distintos a Idealista/Fotocasa: regimen, periodo minimo, contacto...), pero
aqui se hace la clasificacion clave para tu comparativa de estrategias:
    - regimen 'A'  (vivienda en alquiler completo)      -> tipo_oferta = piso_completo
    - regimen 'CO' (completar vivienda, ya hay ocupantes)-> tipo_oferta = habitacion

Tambien se separa precio_total (si es piso completo) de precio_habitacion
(si es alquiler por habitacion), porque no son comparables directamente.

Salida: ua_limpio.csv
"""

import re
import os
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
RAW_DIR = SCRIPT_DIR.parent
OUT_DIR = SCRIPT_DIR.parent / "limpio"


def parse_precio(txt):
    """Se queda con el PRIMER importe en euros que aparezca (algunos campos
    traen dos precios, p.ej. '1200€ / 300€ hab.' -> nos quedamos con 1200,
    el precio del piso completo; el precio por habitacion queda en el texto
    original para quien quiera revisarlo)."""
    if pd.isna(txt) or txt == "":
        return None
    txt = str(txt)
    m = re.search(r"([\d]{1,3}(?:\.[\d]{3})*|\d+)(?:,(\d+))?\s*€", txt)
    if not m:
        return None
    entero = m.group(1).replace(".", "")
    decimales = m.group(2) or "0"
    try:
        return float(f"{entero}.{decimales}")
    except ValueError:
        return None


PALABRAS_HABITACION = [
    "compañer", "una persona más", "una persona mas", "otra persona",
    "buscamos", "busco", "completar", "compartid",
]


def clasificar_tipo_oferta(regimen, precio_num, observaciones):
    """
    OJO: el campo 'regimen' del origen (A = vivienda en alquiler, CO = completar
    vivienda con ocupantes ya dentro) NO es fiable por si solo para saber si el
    precio publicado es del piso completo o de una sola habitacion. En la
    practica hay muchos anuncios en regimen 'A' donde el texto deja claro que
    se busca "una persona mas" para completar el piso, y el precio publicado
    es el de esa habitacion suelta (habitualmente 200-450 €), no el alquiler
    total del piso (que en esta muestra arranca en ~750 €).

    Por eso se combina el regimen con: (a) palabras clave en observaciones que
    delatan que se busca compañero/a, y (b) un umbral de precio (600 €) que,
    en esta muestra, separa con bastante limpieza los precios de habitacion
    suelta (max. 450 €) de los de piso completo (min. 750 €).
    """
    regimen = str(regimen).strip().upper()
    obs = str(observaciones).lower()

    si_hay_palabra_clave = any(p in obs for p in PALABRAS_HABITACION)

    if regimen == "CO":
        return "habitacion"
    if regimen == "A":
        if si_hay_palabra_clave:
            return "habitacion (regimen A pero texto indica precio por habitacion)"
        if pd.notna(precio_num) and precio_num < 600:
            return "habitacion (regimen A pero precio bajo sugiere por habitacion)"
        return "piso_completo"
    return "otro"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    df = pd.read_csv(f"{RAW_DIR}/ua_bolsa_alojamiento_san_vicente_raw.csv", sep=";", dtype=str)

    out = pd.DataFrame(index=df.index)
    out["habitaciones"] = pd.to_numeric(df["habitaciones"], errors="coerce")
    out["plazas"] = pd.to_numeric(df["plazas"], errors="coerce")
    out["tipo_vivienda"] = df["tipo"]  # P/A/E/C/T/B (piso/apto/estudio/casa/chalet/bungalow)
    out["regimen"] = df["regimen"]
    out["direccion"] = df["direccion"]
    out["precio_declarado"] = df["precio"]
    out["precio_num"] = df["precio"].apply(parse_precio)
    out["tipo_oferta"] = [
        clasificar_tipo_oferta(r, p, o)
        for r, p, o in zip(df["regimen"], out["precio_num"], df["observaciones"])
    ]
    out["tipo_oferta_simplificado"] = out["tipo_oferta"].apply(
        lambda t: "habitacion" if str(t).startswith("habitacion") else t
    )

    # Caso especial: el precio principal es del piso entero pero el texto
    # menciona ademas el precio de la habitacion suelta (p.ej. "315€/habitación").
    # Ahi el precio correcto a usar como "habitacion" es el que va con "/habitaci",
    # no el precio_num original (que es el del piso completo).
    def precio_por_habitacion_si_aplica(tipo_simpl, precio_num, obs):
        if tipo_simpl != "habitacion":
            return precio_num
        m = re.search(r"([\d.,]+)\s*€\s*/\s*habitaci", str(obs), re.IGNORECASE)
        if m:
            val = m.group(1).replace(".", "").replace(",", ".")
            try:
                return float(val)
            except ValueError:
                pass
        return precio_num

    out["precio_num"] = [
        precio_por_habitacion_si_aplica(t, p, o)
        for t, p, o in zip(out["tipo_oferta_simplificado"], out["precio_num"], df["observaciones"])
    ]
    out["periodo_minimo_meses"] = pd.to_numeric(df["periodo_minimo_meses"], errors="coerce")
    out["fecha_oferta"] = pd.to_datetime(df["fecha_oferta"], format="%d/%m/%Y", errors="coerce")
    out["servicios_incluidos"] = df["servicios_incluidos"]
    out["observaciones"] = df["observaciones"]

    # duplicados internos: mismo contacto+direccion+precio publicados por error dos veces
    out["es_duplicado"] = out.duplicated(subset=["direccion", "precio_num", "tipo_oferta"], keep="first")

    out_path = f"{OUT_DIR}/ua_limpio.csv"
    out.to_csv(out_path, sep=";", index=False)

    print(f"Total filas: {len(out)}")
    print("--- tipo_oferta (detallado) ---")
    print(out["tipo_oferta"].value_counts())
    print("--- tipo_oferta_simplificado ---")
    print(out["tipo_oferta_simplificado"].value_counts())
    print(f"Duplicados internos detectados: {out['es_duplicado'].sum()}")
    hab = out[out["tipo_oferta_simplificado"] == "habitacion"]["precio_num"]
    piso = out[out["tipo_oferta_simplificado"] == "piso_completo"]["precio_num"]
    print(f"Precio medio habitacion (n={hab.count()}): {hab.mean():.0f} €/mes (rango {hab.min():.0f}-{hab.max():.0f})")
    print(f"Precio medio piso completo (n={piso.count()}): {piso.mean():.0f} €/mes (rango {piso.min():.0f}-{piso.max():.0f})")
    print(f"Guardado en: {out_path}")


if __name__ == "__main__":
    main()

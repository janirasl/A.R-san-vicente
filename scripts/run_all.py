"""
Ejecuta toda la cadena del proyecto en el orden correcto, de crudo a resultado.

Por que existe: hay 14 scripts y el orden importa (los modelos leen los limpios,
y los limpios leen los crudos). Este fichero es la unica forma soportada de
reproducir el proyecto entero:

    python3 scripts/run_all.py

No toca nada de raw/. Todo lo que hay en limpio/, eda/, powerbi/ y graficos/
se regenera desde cero, asi que si algo de esas carpetas se pierde, se
recupera ejecutando esto.

_captura_20260910.py NO esta en la lista a proposito: es una extraccion puntual
que ya dio su CSV en raw/ y volver a lanzarla no aporta nada.
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

FASES = [
    ("1. Limpieza de datos crudos", [
        "limpieza_alquiler_residencial.py",
        "limpieza_venta.py",
        "limpieza_ua.py",
        "limpieza_turistico.py",
        "limpieza_turistico_ampliado.py",
        "limpieza_turistico_habitaciones.py",
    ]),
    ("2. Unificacion", [
        "unificar_datasets.py",
    ]),
    ("3. EDA y modelo", [
        "eda_exploratorio.py",
        "modelo_financiero.py",
        "punto_equilibrio_dias.py",
        "serie_temporal_estrategias.py",
    ]),
    ("4. Robustez y validacion", [
        "sensibilidad_estacionalidad.py",
        "validacion_indice_mercado.py",
        "sesgo_duracion.py",
    ]),
]


def main():
    fallos = []
    for fase, scripts in FASES:
        print(f"\n{'='*84}\n{fase}\n{'='*84}")
        for s in scripts:
            print(f"\n>>> {s}")
            r = subprocess.run([sys.executable, str(SCRIPT_DIR / s)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                fallos.append(s)
                print(f"    FALLO (codigo {r.returncode})")
                print(r.stderr[-1500:])
            else:
                # solo la ultima linea util, para que la salida sea legible
                utiles = [l for l in r.stdout.strip().split("\n") if l.strip()]
                print("    OK  " + (utiles[-1][:100] if utiles else ""))

    print(f"\n{'='*84}")
    if fallos:
        print(f"TERMINADO CON {len(fallos)} FALLO(S): {', '.join(fallos)}")
        sys.exit(1)
    print("TERMINADO SIN ERRORES. limpio/, eda/, powerbi/ y graficos/ estan al dia.")


if __name__ == "__main__":
    main()

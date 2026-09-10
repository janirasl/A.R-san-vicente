# Archivo

Nada de esto se ha borrado: son ficheros superados por versiones posteriores, que se conservan aquí para poder rastrear de dónde vino cada dato. Ninguno lo lee ya la cadena de scripts.

Antes de mover cada uno se comprobó que su contenido está también en otro sitio. Eso es lo que dice la columna "dónde está ahora".

| Fichero | Qué era | Por qué se archiva | Dónde está ahora |
|---|---|---|---|
| `fotocasa_san_vicente_raw_con_grupo.csv` | Captura de Fotocasa del 24-08 con dos columnas derivadas añadidas (`grupo_comparacion`, `precio_m2_eur`) | Es la misma captura que `raw/fotocasa_san_vicente_raw_2026-08-24.csv` más dos columnas calculables. Comprobado: los datos comunes coinciden exactamente (`.equals()` → True) | `raw/fotocasa_san_vicente_raw_2026-08-24.csv` |
| `ua_bolsa_alojamiento_san_vicente_raw_2026-08-24.csv` | Volcado de la Bolsa de Alojamiento de la UA, 41 filas | 39 de sus 40 direcciones están también en la versión de 45 filas, que además trae contacto, teléfono y servicios incluidos | `raw/ua_bolsa_alojamiento_san_vicente_raw.csv` |
| `alquiler_ua_bolsa_san_vicente.csv` | Resumen manual de 6 filas de la bolsa de la UA | Primer volcado a mano, sustituido por la extracción completa de 45 filas | `raw/ua_bolsa_alojamiento_san_vicente_raw.csv` |
| `muestra_alquiler_estudiantes.csv` | 10 anuncios de alquiler transcritos a mano | Muestra manual de la primera fase. La cadena la excluye a propósito desde que existe la extracción sistemática de Idealista y Fotocasa | `raw/idealista_san_vicente_raw*.csv` |
| `fuentes_datasets.csv` | Nota de qué mide cada fuente | Recogido y ampliado en prosa | `docs/resumen_recopilacion_datos.md` |
| `cobertura_extraccion.csv` | Cuántos registros se sacaron de cada portal frente al total anunciado | Ídem | `docs/resumen_recopilacion_datos.md` |
| `fotocasa_cobertura.csv` | Ídem, solo Fotocasa | Ídem | `docs/resumen_recopilacion_datos.md` |
| `demanda_universitaria.csv` | Matrícula de la UA y inscritos en PAU | Contexto de demanda potencial; no entra en ningún cálculo | `docs/resumen_recopilacion_datos.md` |
| `sensibilidad_ocupacion.csv` | Barrido de ocupación turística del modelo antiguo | Sustituido por el punto de equilibrio en noches, que responde a lo mismo sin asumir ocupación | `eda/punto_equilibrio_noches.csv` |
| `06_comparativa_neta_roi.png` | Gráfico de ROI neto | **Muestra cifras anteriores a la corrección de costes operativos del turístico.** Equivalente actual, ya corregido | `graficos/09_escenarios_roi.png` |
| `07_sensibilidad_ocupacion.png` | Gráfico del barrido de ocupación | Mismo motivo | `graficos/10_punto_equilibrio_noches.png` |

Además, todo el historial está en git: `git log --follow -- <fichero>` recupera cualquier versión anterior de cualquier fichero del repositorio.

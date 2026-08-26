# EDA y modelo financiero — hallazgos

Resultado del análisis exploratorio (`scripts/eda_exploratorio.py`) y del modelo financiero comparativo (`scripts/modelo_financiero.py`) sobre los 5 CSV limpios. Sigue tu metodología: distribución de precios → comparación de viviendas equivalentes (mismo arquetipo) → ingresos brutos − gastos = ingresos netos → ROI.

## El arquetipo usado para comparar

Para que las 4 estrategias sean comparables hace falta fijar una misma vivienda de referencia. Se eligió **piso de 3 habitaciones, ~90-100 m²**, por ser el más representativo en las tres fuentes a la vez: 46% del alquiler residencial (66/144), el grupo más numeroso en venta (31/99) y el mayoritario en piso completo de la UA (10/17).

| Dato del arquetipo | Valor | Fuente / n |
|---|---|---|
| Precio de compra | 237.950 € (mediana) | venta_limpio, n=22 |
| Alquiler residencial anual | 968 €/mes (mediana) | alquiler_residencial_limpio, n=34 |
| Alquiler por habitación (UA) | 292 €/hab./mes (mediana) | ua_limpio, n=28 |
| Precio/noche turístico (vivienda completa) | 122 €/noche (mediana) | turistico_precios_limpio, n=7 |

## Distribuciones (EDA exploratorio)

- **Alquiler residencial**: precio/m² medio 11,1 €/m²/mes (mediana 10,5), muy por encima del dato oficial SERPAVI (6,4 €/m²/mes) y también del agregador de mercado (7,6 €/m²/mes). Es esperable en parte: la muestra de Idealista se extrajo con filtro "hasta 2.000€, 2-5 hab." y muchos anuncios son de temporada/estudiantes, que suelen cotizar más caro por m² que el alquiler tradicional de larga duración que mide SERPAVI — no es necesariamente un error de los datos, pero conviene mencionarlo como limitación de la muestra en la memoria.
- El precio/m² baja según sube el número de habitaciones (pisos grandes más baratos por m², patrón típico del mercado).
- Se detectaron 4 viviendas con m² claramente mal extraído de la fuente RAW (precio/m² por debajo de 3€, imposible en este mercado) — quedan marcadas (`m2_sospechoso`) y excluidas solo de los cálculos de precio/m², no borradas.
- **Venta**: precio/m² medio 2.273 €/m² excluyendo los 5 outliers de lujo (p95). Apartamento y bungalow salen más caros por m² que piso y chalet/villa en esta muestra — con pocas filas por tipo, tómalo como orientativo, no concluyente.
- **UA bolsa de alojamiento**: habitación suelta 292€/mes (mediana) vs. piso completo 1.050€/mes (mediana) — la relación no es exactamente ×3 porque el piso completo tiene descuento por volumen respecto a sumar 3 habitaciones sueltas.
- **Turístico**: vivienda completa 122€/noche (mediana), habitación/hotel 72€/noche, villas 484€/noche (categoría aparte, no comparable al arquetipo). Con solo 22 anuncios en San Vicente (frente a los cientos de Idealista/Fotocasa), estas cifras tienen más incertidumbre que las de alquiler/venta.

## Comparativa de las 4 estrategias (ingreso NETO y ROI)

Gastos aplicados: IBI estimado (0,767% sobre un valor catastral asumido al 55% del precio de mercado, ya que no hay valor catastral real por vivienda) + comunidad (70€/mes, punto medio del rango 40-100€) + seguro de impago (6,5% del bruto, solo residencial/estudiantil) + comisión de plataforma (10% del bruto, solo turístico). Todos los supuestos están marcados en el propio script (`modelo_financiero.py`) para que los puedas cambiar sin tocar el resto del código.

| Estrategia | Ingreso bruto/año | Gastos/año | Ingreso neto/año | Neto/mes | Yield bruto | **ROI neto** | Payback |
|---|---|---|---|---|---|---|---|
| 1. Residencial anual | 11.610 € | 2.598 € | 9.012 € | 751 € | 4,88% | **3,79%** | 26,4 años |
| 2. Estudiantil x habitación | 10.530 € | 2.528 € | 8.002 € | 667 € | 4,43% | **3,36%** | 29,7 años |
| 3. Turístico (Airbnb/Booking) | 34.363 € | 5.280 € | 29.083 € | 2.424 € | 14,44% | **12,22%** | 8,2 años |
| 4. Mixto (9m estudiantil + 3m turístico) | 16.488 € | 3.216 € | 13.272 € | 1.106 € | 6,93% | **5,58%** | 17,9 años |

*(tabla completa, con más decimales, en `eda/comparativa_estrategias.csv`)*

**El turístico gana claramente en ROI neto antes de impuestos** (12,2% anual, casi el triple que el residencial). El modelo mixto (curso académico + verano turístico) queda en un cómodo segundo puesto, muy por encima de las dos estrategias "puras" de alquiler tradicional.

### Pero hay un matiz fiscal importante

El turístico **no tiene ninguna reducción de IRPF** (tributa el 100% del rendimiento neto), mientras que residencial y estudiantil tienen una reducción del 50% sobre la base imponible (caso general). Eso significa que, aunque el turístico gana en neto antes de impuestos, una parte mayor de ese neto tributa:

| Estrategia | Base imponible IRPF | % del neto que tributa |
|---|---|---|
| 1. Residencial anual | 4.506 € | 50% |
| 2. Estudiantil x habitación | 4.001 € | 50% |
| 3. Turístico | 29.083 € | 100% |
| 4. Mixto | 10.094 € | 76% |

Aun así, con un ROI neto pre-impuestos casi 3-4× superior, el turístico probablemente sigue ganando después de aplicar el IRPF salvo en tramos marginales muy altos — pero para dar una cifra exacta de ROI *después* de impuestos haría falta tu tipo marginal de IRPF (no está en el alcance de datos de mercado que hemos recopilado).

## Limitaciones a mencionar en la memoria

- La deduplicación cruzada Idealista↔Fotocasa/sesiones es heurística (precio+habitaciones+m², sin dirección exacta) — puede haber falsos positivos/negativos.
- La ocupación turística (77%) es un proxy de Alicante ciudad, no un dato específico de San Vicente (el INE no cubre el municipio). Es el supuesto que más impacta el resultado de las estrategias 3 y 4 — por eso se añadió un análisis de sensibilidad (ver sección siguiente).
- IBI, seguro de hogar, mantenimiento y gestión turística no tienen cifra oficial única — se usaron puntos medios de rangos documentados, marcados como `_ASUNCION` en el script.
- El arquetipo de "estudiantil x habitación" asume ocupación completa de las 3 habitaciones los 12 meses; en la práctica el curso universitario no cubre el verano, que es justo el hueco que cubre la estrategia 4 (mixta).
- Muestra turística pequeña (n=22 en San Vicente) frente a las ~250 de alquiler/venta — los precios turísticos tienen más margen de error.

## Análisis de sensibilidad: ¿y si Airbnb no está siempre alquilado?

El modelo base asume el turístico ocupado el 77% del año (~281 noches), pero esa cifra es un **proxy de Alicante ciudad**, no un dato real de San Vicente del Raspeig (el INE no publica ocupación para el municipio — ver limitaciones). Es el supuesto que más pesa en el resultado, así que en vez de quedarnos con un único número se calculó el ROI del turístico y del mixto para ocupaciones entre el 10% y el 90%, y se buscó el punto de equilibrio frente al residencial.

Como el precio de compra, la comisión de plataforma y los gastos fijos son constantes, el ROI de ambas estrategias es una función **lineal** de la ocupación — el punto de equilibrio se puede calcular de forma exacta, no es una aproximación visual.

**Resultado (gráfico `graficos/07_sensibilidad_ocupacion.png`, tabla `eda/sensibilidad_ocupacion.csv`):**

- El turístico deja de ganar al residencial (3,79% ROI) solo si la ocupación real cae **por debajo del 27%** (~99 noches/año, menos de 1 de cada 3 días con la vivienda alquilada).
- El mixto deja de ganar al residencial solo si la ocupación de la parte de verano cae **por debajo del 34,6%**.
- Con el supuesto base (77%), hay bastante margen de seguridad: la ocupación tendría que desplomarse a menos de un tercio de lo asumido para que el alquiler tradicional fuera mejor opción.

Dicho de otra forma: el resultado del turístico como estrategia ganadora **no depende de forma frágil** del 77% asumido — se sostiene incluso con una ocupación bastante más pesimista y realista para un municipio sin playa como San Vicente. Aun así, conviene declarar este supuesto explícitamente en la memoria del proyecto y, si en algún momento consigues una cifra de ocupación real (por ejemplo pidiendo datos a AirDNA o similar, o mirando reseñas/disponibilidad de anuncios concretos en Airbnb/Booking), sustituirla en `OCUPACION_TURISTICA` dentro de `modelo_financiero.py`.

## Cómo reproducir / ajustar

```
cd scripts
python3 eda_exploratorio.py      # distribuciones y graficos/*.png
python3 modelo_financiero.py     # tabla comparativa y graficos/06_comparativa_neta_roi.png
```

Para probar otros supuestos (ocupación turística, comisión de plataforma, comunidad, etc.), cambia las constantes al principio de `modelo_financiero.py` y vuelve a ejecutar — no hace falta tocar el resto del script.

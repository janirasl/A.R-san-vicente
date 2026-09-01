# EDA y modelo financiero — hallazgos

Resultado del análisis exploratorio (`scripts/eda_exploratorio.py`), del modelo financiero por escenarios (`scripts/modelo_financiero.py`) y de la serie temporal mensual (`scripts/serie_temporal_estrategias.py`).

> **Nota de versión.** Este documento recoge el modelo corregido tras una revisión crítica. La versión anterior daba al turístico un ROI del 12,2% porque solo le imputaba una comisión de plataforma del 10% y ningún coste operativo, y porque asumía que el alquiler estudiantil se cobraba 12 meses al año. Ambas cosas estaban mal y se han corregido. Las conclusiones han cambiado de forma sustancial.

## Principio metodológico: datos ≠ supuestos

Todo lo que sigue distingue explícitamente dos cosas:

- **Datos observados** — salen de los CSV limpios del proyecto, cada uno con su tamaño de muestra. Es lo único que se puede defender como "dato de San Vicente del Raspeig". Exportados en `eda/datos_observados.csv`.
- **Supuestos** — hipótesis del modelo. **Ninguna** procede de una medición local. Exportados en `eda/supuestos_modelo.csv`, con su justificación.

### Datos observados (arquetipo: piso 3 hab., ~90-100 m²)

| Concepto | Valor | n | Fuente |
|---|---|---|---|
| Precio de compra | 237.950 € | 22 | `venta_limpio.csv` |
| Alquiler residencial | 990 €/mes | 39 | `alquiler_residencial_limpio.csv` |
| Alquiler por habitación (UA) | 292 €/hab./mes | 28 | `ua_limpio.csv` |
| Precio/noche turístico | 122 €/noche | **7** | `turistico_precios_limpio.csv` |

El arquetipo se eligió por ser el más representativo en las tres fuentes: 46% del alquiler residencial, el grupo más numeroso en venta y el mayoritario en piso completo de la UA.

**Atención al n=7 del precio turístico.** Es, con diferencia, la cifra menos robusta del modelo, y además alimenta la estrategia sobre la que gira toda la conclusión. Debe aparecer siempre con su n al lado, nunca sola.

### Inversión real

La rentabilidad se calcula sobre **dos denominadores**, porque no son lo mismo:

- Precio de compra: 237.950 €
- **Inversión total desembolsada: 264.124 €** (compra + ~11% de ITP, notaría, registro y gestoría)

La segunda es la que refleja el dinero que realmente sale del bolsillo, y es la que se usa como referencia principal.

## Lo que faltaba: los costes operativos del turístico

Este es el cambio más importante del modelo. El alquiler vacacional no es alquiler residencial con más ingresos: tiene una estructura de costes completamente distinta, y el modelo anterior la ignoraba casi por completo.

| Coste | Escenario pesimista | Base | Optimista |
|---|---|---|---|
| Limpieza entre estancias | 3.283 € | 2.736 € | 2.528 € |
| Suministros (los paga el propietario) | 1.800 € | 1.440 € | 1.200 € |
| Mantenimiento / reposición | 1.406 € | 1.339 € | 1.375 € |
| Gestión | 3.615 € | 2.678 € | 0 € |
| Comisión de plataforma | 3.012 € | 3.213 € | 1.718 € |
| **Total operativo** | **13.116 €** | **11.406 €** | **6.821 €** |
| **% del ingreso bruto** | **65,3%** | **42,6%** | **19,8%** |

Entre el 20% y el 65% del ingreso bruto turístico se va en costes operativos. El modelo anterior contaba un 10%. De ahí venía la sobreestimación.

Dos detalles que suelen pasarse por alto y que aquí sí están: en vacacional **los suministros los paga el propietario** (en residencial los paga el inquilino), y **la limpieza escala con la rotación** — a estancias más cortas, más limpiezas por el mismo número de noches ocupadas.

## Resultados por escenario

Los tres escenarios mueven a la vez ocupación y costes, porque son justo las variables sin dato local:

| Estrategia | Pesimista (oc. 45%) | Base (oc. 60%) | Optimista (oc. 77%) |
|---|---|---|---|
| 1. Residencial anual | **3,30%** | 3,30% | 3,30% |
| 2. Estudiantil x habitación | 2,44% | 2,44% | 2,44% |
| 3. Turístico | 1,94% | **5,12%** | **9,73%** |
| 4. Mixto (curso + verano) | 2,69% | 3,22% | 3,99% |

*(ROI neto anual sobre inversión total; tabla completa en `eda/comparativa_estrategias_escenarios.csv`)*

**El resultado ya no es "el turístico gana".** En el escenario pesimista, el residencial es la mejor opción — el turístico cae al último puesto, porque sus costes fijos y operativos no bajan proporcionalmente cuando cae la ocupación.

### Umbrales de decisión

A partir de qué ocupación el turístico supera al residencial, según la estructura de costes:

| Estructura de costes | El turístico gana a partir de |
|---|---|
| Pesimista (gestión externalizada, estancias cortas, comisión alta) | **63,5%** de ocupación |
| Base | **42,9%** de ocupación |
| Optimista (autogestión, estancias largas, Airbnb split-fee) | **31,5%** de ocupación |

Esto es lo verdaderamente interesante del análisis: la decisión no depende solo de cuánta ocupación consigas, sino de **cómo gestiones los costes**. Con gestión externalizada necesitas casi dos tercios del año ocupado para batir a un alquiler residencial tranquilo; autogestionando, te basta con un tercio.

## Estacionalidad y horizonte temporal

La serie mensual (`powerbi/flujo_mensual_estrategias.csv`, 30 años × 4 estrategias) usa exactamente los mismos supuestos que el modelo anual — los importa del mismo archivo, así que los dos modelos no pueden contradecirse.

- **Estudiantil**: ocupación alta en curso (sep-jun) y baja en verano (jul-ago). Ya **no** se asume que se cobren 12 meses; esa corrección baja su ROI de 3,36% a 2,44% y la deja como la peor de las cuatro.
- **Turístico**: curva estacional con pico en agosto, media anual igual a la del escenario.
- **Residencial**: 95% todo el año (rotación de inquilinos).

Payback sobre la inversión total, escenario base: turístico 19,7 años, mixto 28,2 años, residencial y estudiantil no la recuperan dentro de los 30 años analizados. El mixto adelanta al residencial en el mes 23.

Ojo: es **payback simple**. No incorpora valor temporal del dinero, inflación, revalorización del inmueble, valor residual ni coste de oportunidad. Sirve para comparar estrategias entre sí sobre la misma vivienda, no para juzgar si comprar es buena inversión frente a otras alternativas.

## Efecto fiscal

El turístico no tiene reducción de IRPF (tributa el 100% del rendimiento neto); residencial y estudiantil tienen la reducción general del 50%. Esto se reporta como **base imponible**, no como rentabilidad después de impuestos — calcular el IRPF real exigiría el tipo marginal de la contribuyente, que no forma parte de los datos de mercado recopilados.

## Conclusión (condicional)

> El alquiler turístico maximiza la rentabilidad **bajo escenarios de ocupación superiores al 31-64%** —según cómo se gestionen los costes operativos—, mientras que el alquiler residencial ofrece menor rentabilidad potencial (3,30%) pero mucha menor exposición a la estacionalidad, a los costes operativos y a la carga de gestión. El alquiler estudiantil por habitaciones, una vez se deja de asumir que se cobra los 12 meses, es la menos rentable de las cuatro (2,44%).
>
> La ocupación turística real de San Vicente del Raspeig **no está medida en este trabajo**: es el supuesto del que depende toda la conclusión.

## Limitaciones

- La deduplicación cruzada Idealista↔Fotocasa es heurística (precio + habitaciones + m², sin dirección exacta): los portales no publican la calle en las páginas de resultados.
- Ninguna ocupación del modelo (residencial 95%, estudiantil 95/30%, turística 45-77%) procede de una serie histórica local. Son supuestos.
- Los costes operativos turísticos son estimaciones de mercado, no presupuestos pedidos a proveedores de la zona. Afinarlos requeriría pedir precios reales a una gestora y a un servicio de limpieza locales.
- El IBI se estima aplicando el tipo oficial (0,767%) sobre un valor catastral supuesto al 55% del de mercado. El valor catastral real de una vivienda concreta puede diferir bastante.
- No se incluye el coste de puesta a punto inicial (amueblar y equipar), que es sensiblemente mayor en turístico que en residencial y penalizaría más al turístico en los primeros años.
- Muestra turística pequeña (n=7 para el precio del arquetipo).
- El umbral de 600 € que separa habitación de piso completo en los datos de la UA es una regla heurística calibrada sobre esta muestra concreta, no una verdad general.

## Cómo reproducir / ajustar

```
cd scripts
python3 eda_exploratorio.py           # distribuciones y graficos/*.png
python3 modelo_financiero.py          # escenarios, umbrales y eda/*.csv
python3 serie_temporal_estrategias.py # serie mensual para Power BI
```

Todos los supuestos están agrupados al principio de `modelo_financiero.py`, en un bloque marcado como tal. `serie_temporal_estrategias.py` los importa de ahí, así que basta con cambiarlos en un sitio para que los dos modelos se actualicen a la vez.

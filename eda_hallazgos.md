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
| Precio/noche turístico | 145 €/noche | **4** | `turistico_comparables_arquetipo.csv` |

El arquetipo se eligió por ser el más representativo en las tres fuentes: 46% del alquiler residencial, el grupo más numeroso en venta y el mayoritario en piso completo de la UA.

**Atención al n=4 del precio turístico.** Sigue siendo la cifra menos robusta del modelo y la que sostiene toda la conclusión. Debe aparecer siempre con su n al lado, nunca sola. La sección siguiente explica por qué ese n es tan bajo — y por qué no es un problema de método.

## Por qué el n turístico es tan pequeño: el mercado, no la extracción

Se hizo una segunda captura (2026-09-01) mucho mejor diseñada que la primera:

- **Búsqueda acotada por coordenadas** del municipio en lugar de por texto. Buscar "San Vicente del Raspeig" en Airbnb devuelve *"más de 1.000 alojamientos"*, pero casi todos están en Alicante capital, San Juan o Mutxamel. Acotando por el rectángulo del municipio, el resultado real es **10-14 alojamientos enteros**.
- **Filtro de alojamiento entero**, que es lo que corresponde a la estrategia modelada.
- **Tres fechas** (febrero, octubre y julio), lo que multiplica las observaciones y, sobre todo, permite medir la estacionalidad sobre la misma vivienda.
- **Booking como segunda fuente**: con filtro de apartamentos en el municipio, Booking encuentra literalmente **2 alojamientos** en San Vicente. Todo lo demás que muestra está a 3-9 km, en Alicante.

Resultado: 26 observaciones en San Vicente, **16 propiedades únicas**. Y aquí está el hallazgo importante:

| Composición del parque turístico (alojamiento entero) | Propiedades |
|---|---|
| Villas, chalets, adosados y casas rurales | **9** |
| Pisos, apartamentos y lofts | 7 |

**Más de la mitad del alquiler turístico de San Vicente son villas y chalets con piscina para grupos grandes**, no pisos. Coincide con el registro oficial VUT, que da una superficie media de 174 m² y 6,4 plazas. De los pisos, solo **5 propiedades** son de 3-4 dormitorios, y una de ellas tiene piscina en la azotea (producto premium, 199-279 €/noche según plataforma). Quedan **4 pisos realmente comparables** al arquetipo, con precios de 118 a 151 €/noche.

Esto no es una limitación de la extracción: **es el tamaño real del mercado**. Y tiene una consecuencia de fondo para el proyecto: convertir un piso estándar de 90-100 m² en alquiler turístico en San Vicente significa entrar en un mercado donde casi no hay producto comparable, dominado por villas que compiten por otro tipo de cliente. Con 4 comparables no se puede hablar de "precio de mercado" en sentido estadístico; es un rango orientativo.

### Estacionalidad real (medida, no asumida)

Como varias propiedades aparecen en las tres fechas, se puede medir la variación de precio sobre la **misma vivienda**:

| Propiedad | Feb | Jul | Variación |
|---|---|---|---|
| Villa Sensation Seasons (10 dorm.) | 1.006 €/n | 1.765 €/n | **+75%** |
| Villa Mulet (3 dorm., piscina) | 271 €/n | 351 €/n | **+30%** |
| Alojamiento rural con piscina | 157 €/n | 180 €/n | +15% |
| Bungalow Navarro | 163 €/n | 163 €/n | 0% |
| Apartamento 4 dorm. | 151 €/n | 150 €/n (oct) | −1% |
| Loft junto a la Universidad | 105 €/n | 91 €/n (oct) | −13% |

**Los pisos no tienen prima de verano; las villas sí.** Esto sugiere que la demanda turística de pisos en San Vicente no es de playa/vacaciones, sino ligada a la universidad (familias de visita, profesorado, congresos), que se reparte de otra forma a lo largo del año. Es un argumento para revisar la curva estacional asumida en `serie_temporal_estrategias.py`, que da al piso un pico de verano que los datos no respaldan.

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
| Mantenimiento / reposición | 1.670 € | 1.590 € | 1.633 € |
| Gestión | 4.293 € | 3.180 € | 0 € |
| Comisión de plataforma | 3.578 € | 3.816 € | 2.041 € |
| **Total operativo** | **14.624 €** | **12.763 €** | **7.401 €** |
| **% del ingreso bruto** | **61,3%** | **40,1%** | **18,1%** |

Entre el 18% y el 61% del ingreso bruto turístico se va en costes operativos. El modelo anterior contaba un 10%. De ahí venía la sobreestimación.

Dos detalles que suelen pasarse por alto y que aquí sí están: en vacacional **los suministros los paga el propietario** (en residencial los paga el inquilino), y **la limpieza escala con la rotación** — a estancias más cortas, más limpiezas por el mismo número de noches ocupadas.

## Resultados por escenario

Los tres escenarios mueven a la vez ocupación y costes, porque son justo las variables sin dato local:

| Estrategia | Pesimista (oc. 45%) | Base (oc. 60%) | Optimista (oc. 77%) |
|---|---|---|---|
| 1. Residencial anual | **3,30%** | 3,30% | 3,30% |
| 2. Estudiantil x habitación | 2,44% | 2,44% | 2,44% |
| 3. Turístico | 2,80% | **6,51%** | **11,95%** |
| 4. Mixto (curso + verano) | 2,84% | 3,45% | 4,36% |

*(ROI neto anual sobre inversión total; tabla completa en `eda/comparativa_estrategias_escenarios.csv`)*

**El resultado ya no es "el turístico gana".** En el escenario pesimista el residencial es la mejor opción y el turístico queda por detrás incluso del mixto, porque sus costes fijos y operativos no bajan proporcionalmente cuando cae la ocupación. Solo a partir del escenario base el turístico despega, y en el optimista dobla holgadamente al residencial. Toda la distancia entre "3ª opción" y "mejor opción con diferencia" la explican dos supuestos que no están medidos: la ocupación y la estructura de costes.

### Umbrales de decisión

A partir de qué ocupación el turístico supera al residencial, según la estructura de costes:

| Estructura de costes | El turístico gana a partir de |
|---|---|
| Pesimista (gestión externalizada, estancias cortas, comisión alta) | **50,5%** de ocupación |
| Base | **35,2%** de ocupación |
| Optimista (autogestión, estancias largas, Airbnb split-fee) | **26,2%** de ocupación |

Esto es lo verdaderamente interesante del análisis: la decisión no depende solo de cuánta ocupación consigas, sino de **cómo gestiones los costes**. Con gestión externalizada necesitas la mitad del año ocupado para batir a un alquiler residencial tranquilo; autogestionando, te basta con algo más de un cuarto.

## Estacionalidad y horizonte temporal

La serie mensual (`powerbi/flujo_mensual_estrategias.csv`, 30 años × 4 estrategias) usa exactamente los mismos supuestos que el modelo anual — los importa del mismo archivo, así que los dos modelos no pueden contradecirse.

- **Estudiantil**: ocupación alta en curso (sep-jun) y baja en verano (jul-ago). Ya **no** se asume que se cobren 12 meses; esa corrección baja su ROI de 3,36% a 2,44% y la deja como la peor de las cuatro.
- **Turístico**: curva estacional con pico en agosto, media anual igual a la del escenario.
- **Residencial**: 95% todo el año (rotación de inquilinos).

Payback sobre la inversión total, escenario base: turístico 15,4 años, mixto 28,9 años, residencial 30,3 años y estudiantil 41,0 años.

Ojo: es **payback simple**. No incorpora valor temporal del dinero, inflación, revalorización del inmueble, valor residual ni coste de oportunidad. Sirve para comparar estrategias entre sí sobre la misma vivienda, no para juzgar si comprar es buena inversión frente a otras alternativas.

## Efecto fiscal

El turístico no tiene reducción de IRPF (tributa el 100% del rendimiento neto); residencial y estudiantil tienen la reducción general del 50%. Esto se reporta como **base imponible**, no como rentabilidad después de impuestos — calcular el IRPF real exigiría el tipo marginal de la contribuyente, que no forma parte de los datos de mercado recopilados.

## Conclusión (condicional)

> El alquiler turístico maximiza la rentabilidad **bajo escenarios de ocupación superiores al 26-51%** —según cómo se gestionen los costes operativos—, mientras que el alquiler residencial ofrece menor rentabilidad potencial (3,30%) pero mucha menor exposición a la estacionalidad, a los costes operativos y a la carga de gestión. El alquiler estudiantil por habitaciones, una vez se deja de asumir que se cobra los 12 meses, es la menos rentable de las cuatro (2,44%).
>
> La ocupación turística real de San Vicente del Raspeig **no está medida en este trabajo**: es el supuesto del que depende toda la conclusión.

## Limitaciones

- La deduplicación cruzada Idealista↔Fotocasa es heurística (precio + habitaciones + m², sin dirección exacta): los portales no publican la calle en las páginas de resultados.
- Ninguna ocupación del modelo (residencial 95%, estudiantil 95/30%, turística 45-77%) procede de una serie histórica local. Son supuestos.
- Los costes operativos turísticos son estimaciones de mercado, no presupuestos pedidos a proveedores de la zona. Afinarlos requeriría pedir precios reales a una gestora y a un servicio de limpieza locales.
- El IBI se estima aplicando el tipo oficial (0,767%) sobre un valor catastral supuesto al 55% del de mercado. El valor catastral real de una vivienda concreta puede diferir bastante.
- No se incluye el coste de puesta a punto inicial (amueblar y equipar), que es sensiblemente mayor en turístico que en residencial y penalizaría más al turístico en los primeros años.
- Muestra turística muy pequeña (n=4 pisos comparables), pero no por defecto de método: es el tamaño real del mercado de pisos turísticos del municipio.
- El umbral de 600 € que separa habitación de piso completo en los datos de la UA es una regla heurística calibrada sobre esta muestra concreta, no una verdad general.

## Cómo reproducir / ajustar

```
cd scripts
python3 eda_exploratorio.py           # distribuciones y graficos/*.png
python3 modelo_financiero.py          # escenarios, umbrales y eda/*.csv
python3 serie_temporal_estrategias.py # serie mensual para Power BI
```

Todos los supuestos están agrupados al principio de `modelo_financiero.py`, en un bloque marcado como tal. `serie_temporal_estrategias.py` los importa de ahí, así que basta con cambiarlos en un sitio para que los dos modelos se actualicen a la vez.

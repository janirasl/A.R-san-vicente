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
| Alquiler residencial | 960 €/mes | 37 | `alquiler_residencial_limpio.csv` |
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

**Los pisos no tienen prima de verano; las villas sí.** Esto sugiere que la demanda turística de pisos en San Vicente no es de playa/vacaciones, sino ligada a la universidad (familias de visita, profesorado, congresos), que se reparte de otra forma a lo largo del año. **Este hallazgo ya se aplicó al modelo**: la amplitud estacional asumida bajó de ±20 a ±5 puntos de ocupación. Ver la sección siguiente.

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
| 1. Residencial anual | **3,18%** | 3,18% | 3,18% |
| 2. Estudiantil x habitación | 2,44% | 2,44% | 2,44% |
| 3. Turístico | 2,80% | **6,51%** | **11,95%** |
| 4. Mixto (curso + verano) | 2,91% | 3,55% | 4,49% |

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

## El resultado más sólido: punto de equilibrio en noches

Los escenarios de arriba tienen un problema de fondo: parten de "asumo una ocupación del X%", y la ocupación es justo el dato que no tenemos. La conclusión acababa dependiendo de una cifra que me inventé yo.

`scripts/punto_equilibrio_dias.py` invierte la pregunta: parte **solo de precios observados** y despeja cuántas noches al mes hacen falta. La ocupación deja de ser un supuesto de entrada y pasa a ser el resultado.

| Estructura de costes | Noches/mes para igualar al residencial | Al año | Ocupación equivalente |
|---|---|---|---|
| **SUELO — solo comisión documentada** | **6,7** | 80 | 21,9% |
| Costes optimistas | 7,7 | 93 | 25,4% |
| Costes base | 10,4 | 125 | 34,2% |
| Costes pesimistas | 14,9 | 179 | 49,1% |

Y para las otras referencias, con costes base: **8,7 noches/mes** para igualar al estudiantil, y solo **2,9 noches/mes** para cubrir gastos (ROI 0).

**El caso SUELO es la cifra más defendible de todo el proyecto.** Usa únicamente el coste que sí está documentado (la comisión de plataforma, 12%, de las tarifas publicadas de Booking y Airbnb) e ignora limpieza, suministros, gestión y mantenimiento. Es un límite inferior real: pase lo que pase con los costes, **es imposible que el turístico bata al residencial con menos de ~7 noches al mes**. Y ese número no depende de ninguna estimación mía.

El rango realista, por tanto, está entre **7 y 15 noches al mes** (80-179 al año) según cómo se gestionen los costes. Lo que estos datos no responden —y hay que decirlo así en la memoria— es si un piso de 3 habitaciones en San Vicente consigue efectivamente esas noches. Para saberlo habría que mirar la disponibilidad real de los 4-5 pisos que ya operan allí.

## El segmento de temporada no compite con Airbnb

El 72% de los anuncios de Idealista en San Vicente son "alquiler de temporada", así que valía la pena comprobar si ese segmento juega en el mercado residencial o en el turístico. Se consultó Airbnb para un **mes completo** (1 oct → 1 nov), alojamiento entero, acotado al municipio.

| Producto | 3 habitaciones, mes completo |
|---|---|
| Airbnb (El Jazmín, 3 dorm.) | **4.652 €/mes** |
| Alquiler de temporada (Idealista) | 900 €/mes |
| Alquiler anual (Idealista/Fotocasa) | 960 €/mes |

**Airbnb cuesta 5,2 veces más que un alquiler de temporada.** No son productos competidores: el "alquiler de temporada" de los portales está en precio residencial, no en precio turístico, aunque el contrato sea corto. Esto importa para el modelo, porque descarta la idea de que los 41 anuncios de temporada del arquetipo sean oferta turística encubierta.

### Y de paso, una validación independiente del precio turístico

El modelo usa 145 €/noche (n=4), que a mes completo daría **4.408 €** al 100% de ocupación. Airbnb pide **4.652 €** por ese mismo mes en un piso de 3 dormitorios comparable: un desvío del **+6%**.

Es una validación que vale, porque llega desde una superficie de precios distinta —tarifa mensual con descuento aplicado, no precio por noche— y confirma que extrapolar de noche a mes no introduce un sesgo apreciable. El dato está en `airbnb_mensual_san_vicente_2026-09-10.csv`.

## La estacionalidad, corregida

El modelo temporal asumía que la ocupación turística del piso tenía un pico de verano de ±20 puntos sobre la media. **Ese número me lo inventé**, y los datos de la captura de septiembre lo contradicen: midiendo las mismas propiedades en tres fechas, las villas suben mucho en verano (+30% a +75% en precio) pero **los pisos se quedan planos** (−1%) o incluso bajan (−13%). El arquetipo del proyecto es un piso.

La amplitud se ha bajado a **±5 puntos**, coherente con esa evidencia. Sigue siendo un supuesto, pero ahora tiene algo detrás.

Matiz honesto que hay que mantener: lo medido es estacionalidad de **precio**, no de **ocupación**. No son lo mismo. Pero si la demanda estival fuera fuerte, lo normal es que el precio respondiera, como hace en las villas.

**Efecto sobre el resultado** (`scripts/sensibilidad_estacionalidad.py`):

| Amplitud asumida | ROI turístico | ROI mixto |
|---|---|---|
| ±20 pts (original, sin apoyo) | 6,51% | 3,86% |
| ±5 pts (coherente con lo medido) | 6,51% | **3,55%** |
| 0 pts (sin estacionalidad) | 6,51% | 3,45% |

El turístico puro **no se mueve**: cobra los doce meses, y la curva solo redistribuye ocupación entre ellos sin cambiar la media anual — lo que gana en agosto lo pierde en febrero. El mixto sí se mueve, porque solo cobra turístico en julio y agosto: si esos meses dejan de ser el pico, pierde su razón de ser.

Aun así el mixto sigue por encima del residencial (3,55% frente a 3,18%), así que **la conclusión aguanta**. Es un buen ejemplo de análisis de robustez: se comprueba si un resultado depende de un supuesto flojo, y en este caso resulta que no.

## Estacionalidad y horizonte temporal

La serie mensual (`powerbi/flujo_mensual_estrategias.csv`, 30 años × 4 estrategias) usa exactamente los mismos supuestos que el modelo anual — los importa del mismo archivo, así que los dos modelos no pueden contradecirse.

- **Estudiantil**: ocupación alta en curso (sep-jun) y baja en verano (jul-ago). Ya **no** se asume que se cobren 12 meses; esa corrección baja su ROI de 3,36% a 2,44% y la deja como la peor de las cuatro.
- **Turístico**: curva estacional con pico en agosto, media anual igual a la del escenario.
- **Residencial**: 95% todo el año (rotación de inquilinos).

Payback sobre la inversión total, escenario base: turístico 15,4 años, mixto 28,1 años, residencial 31,5 años y estudiantil 41,0 años.

Ojo: es **payback simple**. No incorpora valor temporal del dinero, inflación, revalorización del inmueble, valor residual ni coste de oportunidad. Sirve para comparar estrategias entre sí sobre la misma vivienda, no para juzgar si comprar es buena inversión frente a otras alternativas.

## Efecto fiscal

El turístico no tiene reducción de IRPF (tributa el 100% del rendimiento neto); residencial y estudiantil tienen la reducción general del 50%. Esto se reporta como **base imponible**, no como rentabilidad después de impuestos — calcular el IRPF real exigiría el tipo marginal de la contribuyente, que no forma parte de los datos de mercado recopilados.

## Conclusión (condicional)

> El alquiler turístico maximiza la rentabilidad **bajo escenarios de ocupación superiores al 25-49%** —según cómo se gestionen los costes operativos—, mientras que el alquiler residencial ofrece menor rentabilidad potencial (3,18%) pero mucha menor exposición a la estacionalidad, a los costes operativos y a la carga de gestión. El alquiler estudiantil por habitaciones, una vez se deja de asumir que se cobra los 12 meses, es la menos rentable de las cuatro (2,44%).
>
> La ocupación turística real de San Vicente del Raspeig **no está medida en este trabajo**: es el supuesto del que depende toda la conclusión.

## Limitaciones

- **La deduplicación heurística falla en las dos direcciones, y ahora está medido.**

  *Falsos positivos (fusiona pisos distintos): 10,3%.* Los 90 anuncios de la captura del 10-09 llevan ID de Idealista, así que sabemos con certeza que son 90 pisos diferentes. De ellos, 9 comparten la clave (precio + habitaciones + m²±2) con otro y la heurística los marcaría como duplicados. El caso extremo son **cinco pisos distintos, todos a 900 €/3 hab./90 m²**. Ya está corregido: desde esta captura la deduplicación usa el ID cuando existe, y dos IDs distintos nunca se marcan como duplicados. Recupera esos 9 anuncios (de 176 a 185 únicos).

  *Falsos negativos (no detecta el mismo piso en dos portales).* El anuncio de Calle Bailén aparece el mismo día en Idealista (990 €, 3 hab., 4ª planta, hace 7 horas) y en Fotocasa (990 €, 3 hab., 4ª Planta, hace 7 horas). Es sin duda la misma vivienda. Pero Idealista publica **104 m²** y Fotocasa **95 m²**: 9 m² de diferencia, muy por encima de la tolerancia de ±2. La heurística **no** los empareja, así que ese piso cuenta dos veces. Los portales no miden la superficie igual, y eso rompe cualquier emparejamiento basado en m². Sin corregir: haría falta una tolerancia mucho mayor, que a su vez dispararía los falsos positivos.

- **La clasificación temporada/anual NO es homogénea entre capturas**, y esto afecta a un número de portada. La proporción de anuncios marcados como "alquiler de temporada" en Idealista es del 33% en la captura del 24-ago, 68% en la del 26-ago y 72% en la del 10-sep. Las dos últimas coinciden; la del 24-ago es la discordante, porque detectó la temporada sobre un campo más estrecho. Consecuencia: el arquetipo "anual" se nutre sobre todo de esa captura (38 anuncios frente a 17 y 11), y probablemente arrastra dentro anuncios de temporada mal clasificados. Al medirlo, la dirección resulta ser **la contraria a la que yo suponía**: en esta muestra el alquiler de temporada de 3 hab. tiene una mediana de **900 €/mes** frente a los **960 €/mes** del anual. O sea que la contaminación tiraría del precio hacia abajo, no hacia arriba. Se arregla reextrayendo con un criterio único.
- **Sesgo de duración**: la muestra de alquiler es una foto de anuncios activos, y un anuncio caro permanece visible mucho más tiempo que uno bien de precio. Eso sobre-representa los caros y hace que los 960 €/mes sean probablemente una **sobreestimación** de la renta alcanzable. La dirección del sesgo se conoce; la magnitud no, porque las dos capturas están a solo dos días. Se corregiría acumulando capturas periódicas.
- La serie de Fotocasa de `alquiler_mercado_mensual.csv` **no debe citarse como índice**: sus 12 valores son todos enteros y solo hay tres distintos, lo que no corresponde a un índice publicado. La validación se apoya solo en Idealista.
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

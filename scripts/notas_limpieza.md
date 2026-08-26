# Notas de la fase de limpieza

Qué se limpió junto y por qué, y los hallazgos/limitaciones importantes para la memoria del proyecto.

## Agrupaciones

- **Alquiler residencial**: Idealista + Fotocasa (`limpieza_alquiler_residencial.py`) — mismo mercado, riesgo real de que la misma vivienda esté en ambos portales.
- **Venta**: Idealista + Fotocasa (`limpieza_venta.py`) — misma lógica.
- **UA Bolsa de Alojamiento** (`limpieza_ua.py`) — estructura propia (régimen, periodo mínimo), se limpia sola, pero es donde se clasifica habitación vs. piso completo.
- **Turístico**: VUT, Airbnb y Booking (`limpieza_turistico.py`) — se limpian por separado porque no comparten una clave fiable (Airbnb no da dirección, Booking da nombre/distancia, VUT da dirección pero no precio); solo se normalizan a €/noche para comparar de forma agregada.

## Hallazgos importantes (para tu apartado de metodología)

**La deduplicación cruzada Idealista↔Fotocasa es una heurística, no una certeza.** Al no tener dirección exacta en los datos capturados (Idealista no publica calle en el listado, Fotocasa solo da zona), el script empareja por precio + habitaciones + m² (±2). Encontró 19 posibles duplicados en alquiler y 11 en venta, pero en un mercado donde los precios y metros cuadrados se redondean mucho (900€, 1000€, 90m², 100m²...), parte de esos emparejamientos pueden ser coincidencia y no la misma vivienda. Quedan marcados (`es_duplicado_cruzado`), no borrados, para que los revises tú antes de excluirlos definitivamente — te recomiendo mirar el `texto_original` de cada par antes de decidir.

**El régimen de la UA no es fiable al 100% para separar precio de habitación vs. piso completo.** Muchos anuncios en régimen "A" (que en teoría es "vivienda en alquiler completo") en realidad describen a alguien buscando un compañero/a para completar el piso, con el precio de una sola habitación. El script combina régimen + palabras clave en el texto + un umbral de precio (600€, que separa limpiamente los ~200-450€ de habitación de los ~750-1300€ de piso completo en esta muestra) para reclasificar. Quedan 28 habitación / 17 piso completo (frente a los 10/35 que saldrían de fiarse solo del régimen declarado).

**Venta: hay un outlier de lujo claro.** El precio/m² medio (2.287€) apenas cambia al excluir duplicados y el percentil 95 de precio (2.273€), así que el efecto "chalet de lujo" pesa menos de lo que parecía a primera vista — pero sigue siendo buena práctica excluir esos outliers antes de construir el arquetipo de "piso estándar".

**Turístico: coincidencia real detectada.** "Villa Sensation Seasons mediterránea" (Airbnb, ~985€/noche) y "Mediterranean Seasons Sensation Villa" (Booking, ~1.352€/noche) son, con toda probabilidad, el mismo alojamiento en las dos plataformas — con precios distintos porque cada plataforma cotiza fechas/condiciones distintas. Es un buen ejemplo real de por qué no conviene sumar ingresos potenciales de varias plataformas sin cruzar antes.

## Cómo ejecutar

```
cd scripts
python3 limpieza_alquiler_residencial.py
python3 limpieza_venta.py
python3 limpieza_ua.py
python3 limpieza_turistico.py
```

Cada uno imprime un resumen por consola y guarda su CSV limpio en la carpeta `limpio/`.

## Siguiente paso: EDA

Con estos 5 CSV limpios (`alquiler_residencial_limpio.csv`, `venta_limpio.csv`, `ua_limpio.csv`, `vut_limpio.csv`, `turistico_precios_limpio.csv`) ya se puede pasar al análisis exploratorio: distribuciones de precio por tipo_oferta, precio/m², comparación de las cuatro estrategias sobre un mismo arquetipo de vivienda, etc.

# Guía rápida — importar en Power BI

## Archivos (carpeta `powerbi/`)

- **`flujo_mensual_estrategias.csv`** — la tabla principal. 1.440 filas = 30 años × 12 meses × 4 estrategias. Columnas: `estrategia`, `mes_absoluto` (1-360), `anio`, `mes_calendario` (1-12), `fecha` (fecha real, útil para el eje X), `ocupacion_asumida`, `ingreso_bruto`, `gastos`, `ingreso_neto`, `ingreso_neto_acumulado`, `balance_acumulado` (neto acumulado − inversión inicial), `roi_acumulado`.
- **`cruces_entre_estrategias.csv`** — para cada par de estrategias, si una supera a la otra desde el principio o en qué mes se cruzan de forma definitiva (`hay_cruce`, `mes_cruce`, `anio_cruce`, `ganador`).
- **`payback_por_estrategia.csv`** — en qué mes cada estrategia, por sí sola, recupera la inversión inicial (264.124 € = precio de compra + gastos de compra).

**Del modelo por escenarios (carpeta `eda/`) — importantes para separar datos de supuestos:**

- **`eda/datos_observados.csv`** — las 4 cifras que sí son datos de San Vicente, cada una con su `n` y su fichero de origen. Úsalas siempre con el n visible en el dashboard.
- **`eda/supuestos_modelo.csv`** — todas las hipótesis del modelo (ocupaciones, comisiones, limpieza, suministros, gestión, IBI estimado, fiscalidad) con su justificación. Ninguna es una medición local. Ponlas en una página aparte del informe, o como tooltip, para que nadie las confunda con datos.
- **`eda/comparativa_estrategias_escenarios.csv`** — 3 escenarios × 4 estrategias, con ROI sobre precio de compra y sobre inversión total. Es la tabla principal de conclusiones.
- **`eda/costes_turistico_desglose.csv`** — desglose de los costes operativos del turístico por escenario (limpieza, suministros, mantenimiento, gestión, comisión). Ideal para un gráfico de cascada o de barras apiladas.
- `eda/sensibilidad_ocupacion.csv` — ROI del turístico/mixto según ocupación.

También siguen disponibles como tablas de detalle: `../limpio/*.csv` (viviendas individuales) y `../eda/comparativa_estrategias.csv` (el escenario base, para compatibilidad).

## Cómo importar

Power BI Desktop → **Obtener datos → Texto/CSV** → selecciona cada archivo. No hace falta crear relaciones entre ellos (son independientes), aunque si quieres cruzar `flujo_mensual_estrategias` con `cruces_entre_estrategias` puedes relacionar por `estrategia`.

Tip: en `flujo_mensual_estrategias.csv`, marca la columna `fecha` como tipo **Fecha** y actívala como tabla de fechas (Modelado → Marcar como tabla de fechas) para aprovechar la jerarquía año/mes automática de Power BI.

## Visuales sugeridos

1. **Estacionalidad (qué meses son mejores para cada estrategia)**: gráfico de líneas con `mes_calendario` en el eje X, `ingreso_neto` en Y, y `estrategia` como leyenda — filtra `anio = 1` para ver un solo ciclo de 12 meses. Verás el pico de verano del turístico y del mixto, y el valle de verano del estudiantil.
2. **Ventaja en el tiempo (a partir de cuándo compensa cada estrategia)**: gráfico de líneas con `mes_absoluto` (o `fecha`) en X, `ingreso_neto_acumulado` en Y, `estrategia` como leyenda. Añade una línea de referencia horizontal en la inversión inicial (264.124 €) para ver el payback de un vistazo.
3. **Matriz/heatmap mes × estrategia**: tabla dinámica con `mes_calendario` en filas, `estrategia` en columnas, `ingreso_neto` como valor, con formato condicional (escala de color) — de un vistazo se ve qué estrategia manda cada mes.
4. **Tarjetas KPI de payback**: usa `payback_por_estrategia.csv` para 4 tarjetas con el año de recuperación de cada estrategia.
5. **Tabla de cruces**: `cruces_entre_estrategias.csv` tal cual, como tabla de texto — responde directamente "a partir de cuánto tiempo cada alquiler tiene ventaja sobre otro".

6. **Escenarios turísticos**: barras agrupadas con `estrategia` en el eje y `escenario` como leyenda, usando `comparativa_estrategias_escenarios.csv` — se ve de un vistazo que el turístico gana en base/optimista pero pierde contra el residencial en el pesimista.
7. **Composición de costes del turístico**: barras apiladas con `costes_turistico_desglose.csv` — muestra que entre el 20% y el 65% del ingreso bruto se va en costes operativos.
8. **Página de metodología**: una tabla con `datos_observados.csv` y otra con `supuestos_modelo.csv`, tituladas explícitamente "Datos observados" y "Supuestos del modelo". Esto vale mucho en una defensa o una entrevista: demuestra que sabes qué has medido y qué has asumido.

## Recordatorio de los supuestos (para un tooltip o página de notas en el informe)

Todas las estrategias llevan ahora un supuesto de ocupación/vacancia, no solo el turístico:

- Residencial anual: 95% de ocupación todo el año (rotación de inquilinos).
- Estudiantil por habitación: 95% en curso académico (sep-jun), 30% en verano (jul-ago).
- Turístico: curva estacional con pico en agosto, calibrada para que la media anual sea el 77% ya documentado (proxy de Alicante, sin dato real de San Vicente).
- Mixto: la de estudiantil en curso + la de turístico en verano.

Estos supuestos están en `scripts/serie_temporal_estrategias.py` (constantes al principio del archivo) — cámbialos y vuelve a ejecutar el script para regenerar los CSV con otros supuestos.

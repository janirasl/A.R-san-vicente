# Guía rápida — importar en Power BI

## Archivos (carpeta `powerbi/`)

- **`flujo_mensual_estrategias.csv`** — la tabla principal. 1.440 filas = 30 años × 12 meses × 4 estrategias. Columnas: `estrategia`, `mes_absoluto` (1-360), `anio`, `mes_calendario` (1-12), `fecha` (fecha real, útil para el eje X), `ocupacion_asumida`, `ingreso_bruto`, `gastos`, `ingreso_neto`, `ingreso_neto_acumulado`, `balance_acumulado` (neto acumulado − inversión inicial), `roi_acumulado`.
- **`cruces_entre_estrategias.csv`** — para cada par de estrategias, si una supera a la otra desde el principio o en qué mes se cruzan de forma definitiva (`hay_cruce`, `mes_cruce`, `anio_cruce`, `ganador`).
- **`payback_por_estrategia.csv`** — en qué mes cada estrategia, por sí sola, recupera la inversión inicial (264.124 € = precio de compra + gastos de compra).

También siguen disponibles (de la fase de EDA anterior, útiles como tablas de contexto/filtro): `../limpio/*.csv` (viviendas individuales) y `../eda/comparativa_estrategias.csv` (resumen anual simplificado).

## Cómo importar

Power BI Desktop → **Obtener datos → Texto/CSV** → selecciona cada archivo. No hace falta crear relaciones entre ellos (son independientes), aunque si quieres cruzar `flujo_mensual_estrategias` con `cruces_entre_estrategias` puedes relacionar por `estrategia`.

Tip: en `flujo_mensual_estrategias.csv`, marca la columna `fecha` como tipo **Fecha** y actívala como tabla de fechas (Modelado → Marcar como tabla de fechas) para aprovechar la jerarquía año/mes automática de Power BI.

## Visuales sugeridos

1. **Estacionalidad (qué meses son mejores para cada estrategia)**: gráfico de líneas con `mes_calendario` en el eje X, `ingreso_neto` en Y, y `estrategia` como leyenda — filtra `anio = 1` para ver un solo ciclo de 12 meses. Verás el pico de verano del turístico y del mixto, y el valle de verano del estudiantil.
2. **Ventaja en el tiempo (a partir de cuándo compensa cada estrategia)**: gráfico de líneas con `mes_absoluto` (o `fecha`) en X, `ingreso_neto_acumulado` en Y, `estrategia` como leyenda. Añade una línea de referencia horizontal en la inversión inicial (264.124 €) para ver el payback de un vistazo.
3. **Matriz/heatmap mes × estrategia**: tabla dinámica con `mes_calendario` en filas, `estrategia` en columnas, `ingreso_neto` como valor, con formato condicional (escala de color) — de un vistazo se ve qué estrategia manda cada mes.
4. **Tarjetas KPI de payback**: usa `payback_por_estrategia.csv` para 4 tarjetas con el año de recuperación de cada estrategia.
5. **Tabla de cruces**: `cruces_entre_estrategias.csv` tal cual, como tabla de texto — responde directamente "a partir de cuánto tiempo cada alquiler tiene ventaja sobre otro".

## Recordatorio de los supuestos (para un tooltip o página de notas en el informe)

Todas las estrategias llevan ahora un supuesto de ocupación/vacancia, no solo el turístico:

- Residencial anual: 95% de ocupación todo el año (rotación de inquilinos).
- Estudiantil por habitación: 95% en curso académico (sep-jun), 30% en verano (jul-ago).
- Turístico: curva estacional con pico en agosto, calibrada para que la media anual sea el 77% ya documentado (proxy de Alicante, sin dato real de San Vicente).
- Mixto: la de estudiantil en curso + la de turístico en verano.

Estos supuestos están en `scripts/serie_temporal_estrategias.py` (constantes al principio del archivo) — cámbialos y vuelve a ejecutar el script para regenerar los CSV con otros supuestos.

# Guía Power BI — qué importar y qué montar

Actualizada tras las correcciones del modelo (costes operativos del turístico, escenarios, punto de equilibrio en noches). Todas las rutas son relativas a la carpeta del proyecto.

---

## 1. Los 6 CSV que necesitas sí o sí

Si solo vas a importar unos pocos, que sean estos:

| Archivo | Filas | Para qué sirve |
|---|---|---|
| `eda/punto_equilibrio_noches.csv` | 12 | **El resultado principal.** Cuántas noches/mes necesita el turístico para batir a cada alternativa, según estructura de costes |
| `eda/comparativa_estrategias_escenarios.csv` | 12 | ROI de las 4 estrategias en los 3 escenarios, sobre precio de compra y sobre inversión total |
| `eda/datos_observados.csv` | 4 | Las únicas 4 cifras que son datos reales de San Vicente, cada una con su `n` |
| `eda/supuestos_modelo.csv` | ~32 | Todas las hipótesis del modelo, separadas de los datos |
| `powerbi/flujo_mensual_estrategias.csv` | 1.440 | Serie mensual a 30 años × 4 estrategias (estacionalidad y acumulado) |
| `eda/costes_turistico_desglose.csv` | 3 | Desglose de los costes operativos del turístico por escenario |

## 2. Complementarios

| Archivo | Para qué |
|---|---|
| `powerbi/payback_por_estrategia.csv` | Año de recuperación de la inversión, para tarjetas KPI |
| `powerbi/cruces_entre_estrategias.csv` | En qué mes cada estrategia adelanta a otra |
| `eda/sensibilidad_ocupacion.csv` | ROI del turístico/mixto barriendo ocupación del 10% al 90% |
| `limpio/turistico_estacionalidad.csv` | Variación de precio real por temporada, medida sobre la misma vivienda |
| `limpio/turistico_comparables_arquetipo.csv` | Los 4-5 pisos turísticos comparables al arquetipo |

## 3. Detalle vivienda a vivienda (para distribuciones y filtros)

`limpio/alquiler_residencial_limpio.csv` (144), `limpio/venta_limpio.csv` (99), `limpio/ua_limpio.csv` (45), `limpio/turistico_ampliado_limpio.csv` (36), `limpio/vut_limpio.csv` (101).

**No importes**: los `*_raw*.csv` de la raíz (son para reproducir la limpieza), los `*_con_marcas.csv` (versiones de auditoría con duplicados) ni `limpio/turistico_precios_limpio.csv` (captura antigua, sustituida por la ampliada).

---

## Cómo importar

Power BI Desktop → **Obtener datos → Texto/CSV**.

Ojo con dos cosas:

- Los CSV de `limpio/` y `eda/` usan **punto y coma** como separador. Power BI suele detectarlo, pero si ves todo en una columna, cámbialo a mano en el cuadro de importación.
- `powerbi/flujo_mensual_estrategias.csv` usa **coma**. Es el único.
- En `flujo_mensual_estrategias`, marca `fecha` como tipo Fecha y actívala como tabla de fechas (Modelado → Marcar como tabla de fechas) para tener jerarquía año/mes automática.

No hace falta crear relaciones: son tablas independientes. Si quieres cruzarlas, la clave común es `estrategia`.

---

## Qué montar, por pregunta

**"¿Cuántas noches necesita el turístico para compensar?"** ← la pregunta central
Gráfico de barras horizontales con `punto_equilibrio_noches.csv`: `estructura_costes` en el eje, `noches_mes` como valor, `objetivo` como filtro o segmentación. Destaca la fila **SUELO**: es el mínimo absoluto (6,9 noches/mes) y es el único que no depende de estimaciones.

**"¿Qué estrategia rinde más?"**
Barras agrupadas con `comparativa_estrategias_escenarios.csv`: `estrategia` en el eje, `roi_neto_s_inversion_total` como valor, `escenario` como leyenda. Se ve que el orden cambia según el escenario, que es justo el mensaje.

**"¿A dónde se va el dinero en el turístico?"**
Barras apiladas o cascada con `costes_turistico_desglose.csv`. Entre el 18% y el 61% del ingreso bruto se va en costes operativos.

**"¿En qué meses gana cada estrategia?"**
Líneas con `flujo_mensual_estrategias.csv`: `mes_calendario` en el eje, `ingreso_neto` como valor, `estrategia` como leyenda, filtrando `anio = 1`. O una matriz mes × estrategia con formato condicional.

**"¿Cuándo recupero la inversión?"**
Líneas con `mes_absoluto` en X y `ingreso_neto_acumulado` en Y, más una línea de referencia en 264.124 € (la inversión total). Complementa con tarjetas KPI de `payback_por_estrategia.csv`.

**Página de metodología** (esta vale mucho en una defensa o entrevista)
Dos tablas enfrentadas: `datos_observados.csv` titulada "Datos observados (San Vicente del Raspeig)" con la columna `n` bien visible, y `supuestos_modelo.csv` titulada "Supuestos del modelo (no medidos)". Deja claro qué mediste y qué asumiste.

---

## Tres avisos para que no te pillen en la defensa

1. **El precio turístico tiene n=4.** Ponlo siempre visible junto a la cifra. No es un fallo de extracción: el municipio solo tiene 4-5 pisos turísticos comparables, el resto del parque son villas.
2. **La ocupación no está medida.** Ninguna conclusión debe redactarse como "el turístico rinde X%", sino como "bajo una ocupación de X, el modelo estima Y". El gráfico de punto de equilibrio es la forma limpia de decirlo.
3. **Los costes operativos (limpieza, suministros, gestión, mantenimiento) son estimaciones propias**, no tarifas reales de proveedores locales. Solo la comisión de plataforma está documentada. Por eso existe el caso SUELO.

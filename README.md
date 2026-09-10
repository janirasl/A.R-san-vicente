# ¿Qué modelo de alquiler renta más en San Vicente del Raspeig?

Análisis comparativo de cinco estrategias de explotación —residencial anual, estudiantil por habitaciones, turístico de piso entero, turístico por habitaciones y mixto— sobre **un mismo arquetipo de vivienda**: piso de 3 habitaciones, 70-130 m², en San Vicente del Raspeig (Alicante).

Datos propios extraídos de Idealista, Fotocasa, Airbnb, Booking, la Bolsa de Alojamiento de la Universidad de Alicante y el registro oficial de viviendas turísticas de la Generalitat Valenciana.

---

## El marco

Una vivienda se puede alquilar **entera o por habitaciones**, y **a largo plazo o por noches**. Son cuatro mercados, no dos, y el proyecto mide los cuatro:

| | Piso entero | Por habitación |
|---|---|---|
| **Largo plazo** | 960 €/mes · n=37 | 292 €/hab./mes · n=28 |
| **Corto plazo** | 145 €/noche · n=4 | 44,8 €/noche · n=15 |

Separar la *unidad* del *plazo* es lo que evita el error más común al mirar Airbnb: comparar el precio de una habitación con el de un piso completo. La columna `unidad` de `dataset_unificado.csv` lo hace explícito.

## Los cuatro resultados que sostienen el trabajo

**1. Entre residencial y estudiantil gana el residencial: 3,18% frente a 2,44% de ROI neto.**
No depende de ningún supuesto de ocupación turística y se apoya en las dos muestras más grandes del proyecto (n=37 y n=28). Es la conclusión más firme.

**2. El turístico necesita 6,7 noches al mes como mínimo absoluto para batir al residencial.**
Esa cifra es un *caso suelo*: se calcula poniendo a cero todos los costes estimados y dejando solo la comisión de plataforma, que sí está documentada. Es un límite inferior matemático — no depende de ninguna suposición. Con una estructura de costes realista hacen falta entre 7 y 15 noches al mes.

**3. Por noches, el piso entero gana a las habitaciones sueltas — siempre.**
6,51% frente a 5,33% en el escenario base, y la ventaja se mantiene en los tres escenarios. Doble penalización: tres habitaciones a 44,8 € ingresan un 7,5% menos que el piso entero a 145 €, y cuestan más de explotar, porque tres habitaciones rotando por separado son el triple de estancias, limpiezas y check-ins para la misma ocupación.

**4. El mercado turístico de pisos en San Vicente casi no existe.**
Búsqueda acotada por coordenadas del municipio: 10-14 alojamientos enteros en Airbnb, 2 en Booking, y de 16 propiedades únicas solo 4-5 son comparables al arquetipo. Las demás son villas y chalets con piscina. Que la muestra turística sea pequeña no es un defecto del método: **es el tamaño real del mercado**.

Los tres, con su nivel de confianza y sus limitaciones, están desarrollados en [`docs/preguntas_analisis.md`](docs/preguntas_analisis.md).

---

## Cómo reproducirlo

```bash
python3 scripts/run_all.py
```

Regenera desde cero `limpio/`, `eda/`, `powerbi/` y `graficos/` a partir de `raw/`. No toca `raw/`.

Requisitos: Python 3.10+, pandas, matplotlib.

---

## Estructura

| Carpeta | Qué hay | ¿Se puede borrar? |
|---|---|---|
| `raw/` | **Las 17 extracciones originales.** Capturas de portales con fecha, más el registro VUT y los índices publicados. | **Nunca.** No se pueden volver a extraer: son fotos de un mercado en una fecha concreta. |
| `limpio/` | Datasets limpios con esquema unificado, uno por fuente, más `dataset_unificado.csv` que los junta todos. | Sí, se regeneran. |
| `eda/` | Tablas de resultado del análisis y del modelo financiero. | Sí, se regeneran. |
| `powerbi/` | Lo que consume el dashboard: serie mensual a 30 años, cruces y payback. Más la guía de montaje. | Sí, se regeneran (la guía no). |
| `graficos/` | Los 11 gráficos del análisis. | Sí, se regeneran. |
| `scripts/` | La cadena completa, 15 scripts. `run_all.py` los lanza en orden. | No. |
| `notebooks/` | Auditoría de calidad (fase 1) y análisis por preguntas (fase 2). | No. |
| `docs/` | Memoria, preguntas de investigación, guía de estudio y notas de recopilación. | No. |
| `_archivo/` | Ficheros superados por versiones posteriores. Se conservan por trazabilidad. | Ver `_archivo/LEEME.md`. |

---

## Por dónde empezar a leer

1. **[`docs/preguntas_analisis.md`](docs/preguntas_analisis.md)** — las seis preguntas de investigación, qué responde cada una, de qué supuestos depende y cuánta confianza merece. Incluye P6: las preguntas que este trabajo **no** puede responder.
2. **[`docs/eda_hallazgos.md`](docs/eda_hallazgos.md)** — el desarrollo completo, hallazgo por hallazgo, con las limitaciones metodológicas.
3. **[`docs/resumen_recopilacion_datos.md`](docs/resumen_recopilacion_datos.md)** — de dónde sale cada dato y qué mide exactamente cada fuente.
4. **[`docs/guia_estudio.html`](docs/guia_estudio.html)** — versión de estudio, con las preguntas incómodas y sus respuestas.

---

## Los ficheros que importan

Si hay que quedarse con cinco:

| Fichero | Qué es |
|---|---|
| `limpio/dataset_unificado.csv` | Tabla de hechos: todos los anuncios de todas las fuentes con esquema común. El punto de entrada para Power BI y para los notebooks. |
| `eda/datos_observados.csv` | Los cuatro datos **medidos** en el municipio, con su n y su fuente. |
| `eda/supuestos_modelo.csv` | Todo lo que el modelo **asume** en vez de medir, separado a propósito del anterior. |
| `eda/comparativa_estrategias_escenarios.csv` | Las 5 estrategias × 3 escenarios. El resultado principal. |
| `eda/punto_equilibrio_noches.csv` | Cuántas noches al mes necesita el turístico para ganar. La métrica que evita asumir una ocupación. |

---

## Decisiones metodológicas que conviene conocer

- **Datos observados y supuestos van en ficheros distintos.** `datos_observados.csv` (4 cifras medidas) y `supuestos_modelo.csv` (todo lo demás). Es lo que permite decir con precisión qué parte de cada conclusión es dato y qué parte es modelo.
- **La deduplicación se hace por ID de anuncio, no por heurística.** La heurística anterior (precio + habitaciones + m²±2) tenía un **10,3% de falsos positivos**, medido contra los IDs reales de la captura de septiembre. Sigue habiendo falsos negativos entre portales: el mismo piso figura con 104 m² en Idealista y 95 m² en Fotocasa.
- **El modelo se invierte en vez de suponer ocupación.** La ocupación turística es el dato que no tenemos. En lugar de inventarlo, se despeja: ¿cuántas noches harían falta? Así la conclusión no depende de una cifra sin fuente.
- **Unidad y plazo son variables separadas.** `unidad` (piso entero / habitación) distingue *qué* se alquila; el mercado distingue *por cuánto tiempo*. Sin esa separación, un promedio inocente mezcla 44,8 €/noche de habitación con 145 €/noche de piso y no significa nada.
- **La muestra propia está validada contra el índice de oferta de Idealista**: 10,25 €/m²/mes frente a 10,7, un desvío del −4,2%.
- **Sesgo conocido y declarado:** la muestra es una foto de anuncios *activos*, y un piso caro permanece publicado más tiempo que uno bien de precio. Eso sobre-representa los caros, así que los 960 €/mes son probablemente una **sobreestimación** de la renta alcanzable.

---

## Lo que falta

- Ocupación real de los pisos turísticos del municipio (el supuesto del que más depende la conclusión). Vía posible: seguimiento del calendario de disponibilidad de los 4-5 pisos que ya operan, o los datos de Inside Airbnb — la petición está redactada en `docs/peticion_inside_airbnb.md`.
- Revalorización del inmueble: el payback solo mide alquiler, no plusvalía. Haría falta el IPV del INE.
- Presupuestos reales de limpieza y gestión en la zona: de los siete parámetros de coste turístico, solo la comisión de plataforma está documentada.
- Comprobar si San Vicente está declarada zona de mercado tensionado (cambia la reducción del IRPF del 50% a hasta el 90%).

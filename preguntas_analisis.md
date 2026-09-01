# Preguntas de investigación

Esqueleto del proyecto: qué se pregunta, con qué se responde, de qué supuestos depende cada respuesta y cuánta confianza merece. Sirve de guion para la memoria y para las páginas del dashboard.

**Objeto de análisis (constante en todas las preguntas):** un mismo arquetipo de vivienda —piso de 3 habitaciones, 70-130 m², en San Vicente del Raspeig— para que la comparación entre modelos de alquiler sea justa. Es el perfil más representativo en las tres fuentes: 46% de la oferta de alquiler, el grupo más numeroso en venta y el mayoritario en piso completo de la UA.

**Datos observados que sostienen todo** (lo único medido en el municipio):

| Concepto | Valor | n | Fuente |
|---|---|---|---|
| Precio de compra | 237.950 € | 22 | Idealista + Fotocasa venta |
| Alquiler residencial | 990 €/mes | 39 | Idealista + Fotocasa alquiler |
| Alquiler por habitación | 292 €/mes | 28 | UA Bolsa de Alojamiento |
| Precio/noche turístico | 145 €/noche | 4 | Airbnb + Booking |

---

## P1. ¿Qué modelo de alquiler es más rentable para una misma vivienda?

La pregunta tal cual **no tiene respuesta única**, y descubrir por qué es uno de los resultados del trabajo. Se parte en dos.

### P1.1 — Entre residencial y estudiantil por habitaciones, ¿cuál rinde más?

- **Métrica:** ingreso neto anual (ingresos brutos − gastos) y ROI sobre inversión total.
- **Datos:** alquiler residencial (n=39) y precio por habitación (n=28). Ambos observados.
- **Supuestos de los que depende:** ocupación residencial 95%, ocupación estudiantil 95% en curso y 30% en verano, seguro de impago 6,5%, comunidad e IBI. Ninguno favorece a una estrategia sobre la otra de forma asimétrica.
- **Respuesta:** **gana el residencial**. 3,30% de ROI neto (8.709 €/año) frente a 2,44% del estudiantil (6.443 €/año).
- **Por qué:** alquilar 3 habitaciones a 292 € da 876 €/mes brutos frente a los 990 € del piso completo, y encima el modelo estudiantil pierde los meses de verano, cuando la demanda universitaria desaparece.
- **Confianza: alta.** Se apoya en las dos muestras más grandes del proyecto y no depende de la ocupación turística, que es el supuesto flojo. **Esta respuesta se sostiene tal cual en la memoria.**

> Ojo con un matiz: la versión anterior del modelo daba 3,36% al estudiantil porque asumía que se cobraban 12 meses al año. Corregir ese error es lo que lo bajó a 2,44% y cambió el orden.

### P1.2 — ¿Dónde encaja el alquiler turístico?

- **Métrica:** **punto de equilibrio en noches** — cuántas noches al mes necesita el turístico para igualar el ingreso neto del residencial. Se eligió esta métrica precisamente porque *no* exige asumir una ocupación: parte de precios observados y despeja las noches.
- **Datos:** precio/noche 145 € (n=4) y el ingreso neto residencial ya calculado.
- **Supuestos:** la estructura de costes operativos. Por eso se calcula un **caso suelo** que usa solo el coste documentado (comisión de plataforma) y pone a cero limpieza, suministros, gestión y mantenimiento.
- **Respuesta:**

| Estructura de costes | Noches/mes necesarias | Al año | Ocupación equivalente |
|---|---|---|---|
| **Suelo (solo comisión documentada)** | **6,9** | 83 | 22,6% |
| Costes optimistas | 7,9 | 95 | 26,1% |
| Costes base | 10,7 | 128 | 35,1% |
| Costes pesimistas | 15,3 | 184 | 50,4% |

- **Confianza: el suelo, alta; el resto, media.** Las 6,9 noches son un límite inferior matemático: es imposible que el turístico bata al residencial con menos, pase lo que pase con los costes. Los otros tres dependen de estimaciones de coste no verificadas localmente.
- **Lo que esta pregunta NO responde:** si un piso de 3 habitaciones en San Vicente consigue de hecho esas noches. Ver P6.

---

## P2. ¿Cómo cambia el ranking según el escenario?

- **Métrica:** ROI neto anual sobre inversión total (264.124 €), en tres escenarios que mueven a la vez ocupación turística y costes operativos.
- **Respuesta:**

| Estrategia | Pesimista (oc. 45%) | Base (oc. 60%) | Optimista (oc. 77%) |
|---|---|---|---|
| Residencial anual | **3,30%** | 3,30% | 3,30% |
| Estudiantil x habitación | 2,44% | 2,44% | 2,44% |
| Turístico | 2,80% | **6,51%** | **11,95%** |
| Mixto (curso + verano) | 2,84% | 3,45% | 4,36% |

- **Lectura:** el orden cambia por completo entre escenarios. En el pesimista gana el residencial y el turístico queda tercero; en el optimista el turístico casi cuadruplica al residencial. **Toda esa distancia la explican dos variables no medidas**: la ocupación y la estructura de costes.
- **Confianza: media.** La estructura del análisis es sólida, pero los valores de ocupación 45% y 60% los fijamos nosotros como rango plausible; solo el 77% tiene origen documentado (proxy de Alicante ciudad). Los costes operativos son estimaciones propias salvo la comisión de plataforma.
- **Conclusión defendible:** *"El turístico maximiza la rentabilidad bajo escenarios de ocupación superiores al 26-51% según la gestión de costes, mientras que el residencial ofrece menor rentabilidad potencial pero mucha menor exposición a la estacionalidad, a los costes operativos y a la carga de gestión."*

---

## P3. Si se compra el piso, ¿en cuántos años se amortiza y con qué modelo?

- **Métrica:** payback simple — años hasta que el ingreso neto acumulado cubre la **inversión total desembolsada** (237.950 € de compra + 26.174 € de ITP, notaría, registro y gestoría = 264.124 €).
- **Respuesta:**

| Estrategia | Pesimista | Base | Optimista |
|---|---|---|---|
| Residencial | 30,3 años | 30,3 | 30,3 |
| Estudiantil | 41,0 años | 41,0 | 41,0 |
| Turístico | 35,8 años | 15,4 | **8,4** |
| Mixto | 35,3 años | 28,9 | 22,9 |

- **Aviso metodológico importante:** es payback **solo del alquiler**. No incluye revalorización del inmueble, valor residual, inflación, valor temporal del dinero ni coste de oportunidad. Por eso salen cifras tan largas: un piso que se amortiza en 30 años vía alquiler puede ser buena inversión igualmente si se revaloriza — pero eso este trabajo no lo mide.
- **Por qué no lo mide:** de venta solo tenemos una foto (agosto 2026), no una serie histórica de precios. Sería necesario el IPV del INE o una serie de Idealista/Fotocasa para la provincia.
- **Confianza: alta en el cálculo, limitada en el alcance.** El número es correcto para lo que mide; lo que hay que cuidar es no presentarlo como "rentabilidad de comprar un piso", que es una pregunta más amplia.

---

## P4. ¿Cómo es realmente el mercado de alquiler turístico en San Vicente?

Esta pregunta no estaba planteada al principio; surgió al intentar ampliar la muestra y resultó ser uno de los hallazgos más relevantes.

- **Método:** búsqueda en Airbnb acotada por coordenadas del municipio (no por texto: buscar "San Vicente del Raspeig" devuelve >1.000 alojamientos, casi todos de Alicante capital), con filtro de alojamiento entero, en tres fechas distintas, más Booking.
- **Respuesta:** el municipio tiene **10-14 alojamientos enteros** en Airbnb y **2** en Booking. De 16 propiedades únicas identificadas, **9 son villas, chalets o adosados** con piscina para grupos grandes y solo 7 son pisos o lofts. De esos, apenas **4-5 son comparables** al arquetipo. Concuerda con el registro oficial VUT: 101 viviendas turísticas registradas, 174 m² de superficie media y 6,4 plazas.
- **Implicación:** convertir un piso estándar en turístico en San Vicente significa entrar en un mercado donde casi no hay producto comparable, dominado por otro tipo de alojamiento y otro tipo de cliente. Y explica por qué n=4 no es un defecto de método: **es el tamaño real del mercado**.
- **Confianza: alta.** Dos fuentes independientes y el registro oficial coinciden.

---

## P5. ¿Hay estacionalidad en los precios turísticos?

- **Método:** como varias propiedades aparecen en las tres fechas consultadas, se mide la variación sobre **la misma vivienda** (no comparando viviendas distintas entre sí, que sería engañoso).
- **Respuesta:** **las villas sí, los pisos no.** Villa Sensation Seasons +75% en julio frente a febrero, Villa Mulet +30%; en cambio el apartamento de 4 dormitorios se queda plano (151 € en febrero, 150 € en octubre) y el loft incluso baja un 13%.
- **Implicación:** la demanda turística de pisos en San Vicente no parece de playa/vacaciones, sino ligada a la universidad —familias de visita, profesorado, congresos—, que se reparte de otra forma a lo largo del año. Esto contradice la curva estacional con pico de verano que asume `serie_temporal_estrategias.py` y que conviene revisar.
- **Confianza: media.** La dirección del hallazgo es clara y consistente, pero son 9 propiedades y 3 fechas puntuales, no una serie.

---

## P6. Preguntas que este trabajo NO puede responder

Listarlas explícitamente es parte del rigor, no una debilidad.

| Pregunta | Por qué no se puede responder | Cómo se resolvería |
|---|---|---|
| **¿Cuál es la ocupación real de un piso turístico en San Vicente?** | El INE solo publica ocupación de municipios declarados "punto turístico" y San Vicente no lo es. Usamos un proxy de Alicante ciudad. **Es el supuesto del que más depende la conclusión.** | Rastrear el calendario de disponibilidad de los 4-5 pisos que ya operan allí durante varios meses, o contratar AirDNA |
| ¿Cuánto se revaloriza la vivienda? | Solo tenemos una foto de precios de venta, sin serie histórica | IPV del INE o serie histórica de un portal |
| ¿Cuánto cuestan limpieza, gestión y suministros en la zona? | Son estimaciones propias; solo la comisión de plataforma está documentada | Pedir presupuesto a una gestora y a un servicio de limpieza locales |
| ¿Está San Vicente declarada zona de mercado tensionado? | No se ha comprobado; afecta a la reducción del IRPF (50% vs hasta 90%) y por tanto a la comparativa | Consultar el registro oficial de zonas tensionadas de la Generalitat |
| ¿Cuál es el valor catastral real del inmueble? | Se estima al 55% del valor de mercado para calcular el IBI | Consulta catastral de un inmueble concreto |

---

## Cómo se traduce en páginas del dashboard

| Página | Pregunta | Ficheros |
|---|---|---|
| 1. El mercado | P4, P5 | `dataset_unificado.csv`, `turistico_estacionalidad.csv` |
| 2. Comparativa de modelos | P1.1, P2 | `comparativa_estrategias_escenarios.csv` |
| 3. ¿Cuántas noches hacen falta? | P1.2 | `punto_equilibrio_noches.csv` |
| 4. Compra y amortización | P3 | `payback_por_estrategia.csv`, `flujo_mensual_estrategias.csv` |
| 5. Metodología | todas | `datos_observados.csv`, `supuestos_modelo.csv` |

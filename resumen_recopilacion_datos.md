# Recopilación de datos — Proyecto de rentabilidad de alquiler en San Vicente del Raspeig

Resumen de toda la información recabada hasta ahora: fuentes oficiales (INE, SERPAVI, VUT), alquiler vacacional/turístico (con precios reales de Airbnb/Booking), extracción de portales de alquiler (Idealista, Fotocasa, UA), anuncios de venta (Idealista, Fotocasa) para la rentabilidad de compra, y gastos/fiscalidad para poder pasar de ingresos brutos a netos. Con esto se cierran los huecos que quedaban pendientes — los datos de mercado están completos para pasar a la siguiente fase. Todos los datos siguen en bruto (RAW), sin depurar ni deduplicar, siguiendo la metodología ya definida en tu proyecto: extracción → clasificación por tipo_oferta → limpieza/deduplicación → comparación de viviendas equivalentes → modelo financiero (ingresos brutos − gastos = ingresos netos → ROI).

## 1. Fuentes oficiales

### SERPAVI (Sistema Estatal de Referencia del Precio del Alquiler)
SERPAVI no publica un único precio de referencia por municipio, sino un rango de valores calculado según la ubicación exacta y las características de cada vivienda (superficie, antigüedad, planta, ascensor, etc.). Para obtenerlo hay una calculadora oficial en **serpavi.mivau.gob.es**, en la que introduces la dirección y los datos de la vivienda y te devuelve un rango de referencia en €/mes. Esto encaja bien con tu metodología de comparar viviendas equivalentes: te recomiendo pasar cada arquetipo de vivienda que uses en el análisis (p. ej. piso de 90 m² / 3 hab. en el centro) por esa calculadora para tener el "precio de referencia oficial" de cada comparable. También hay visores por sección censal, distrito, municipio, provincia y CCAA con datos agregados 2011-2024 descargables en Excel, útiles para contexto histórico.

Como referencia de mercado (no oficial-SERPAVI, sino de un agregador que sí desglosa por municipio), el precio medio de alquiler en San Vicente del Raspeig ronda los **7,6 €/m²/mes en pisos y 9,25 €/m²/mes en casas** (agosto 2026), frente a un precio medio de venta de **~1.697 €/m²**. Conviene contrastar esta cifra con la calculadora oficial de SERPAVI antes de usarla como definitiva en el TFG/proyecto.

Dato oficial ya disponible en tu carpeta (`serpavi_san_vicente.csv`): el precio de referencia SERPAVI real para San Vicente del Raspeig, año 2024, es **6,4 €/m²/mes** (mediana, sobre 2.755 testigos; rango intercuartil 5,2-8,0 €/m²/mes), con un alquiler mediano de 575 €/mes sobre una superficie mediana de 92 m². Esta cifra oficial queda **por debajo** de los 7,6 €/m²/mes del agregador citado arriba — normal, porque son fuentes y metodologías distintas (SERPAVI usa contratos de fianza depositados; el agregador usa anuncios publicados, que tienden a sobrestimar el precio real de mercado). Para el proyecto, usa el dato SERPAVI (6,4 €/m²/mes, o la cifra que te dé la calculadora oficial para tu arquetipo concreto) como referencia legal/oficial, y el del agregador solo como contexto de precio publicado.

### INE — apartamentos turísticos y vivienda
La encuesta de ocupación e índice de precios de apartamentos turísticos del INE se publica a nivel nacional, autonómico, provincial, de zona turística y de **punto turístico**, pero solo cubre los municipios que el INE define expresamente como "puntos turísticos". San Vicente del Raspeig no es uno de ellos (no es un destino de costa/turístico clásico), así que no vas a encontrar cifras de ocupación/precio específicas del municipio en esta operación — es una limitación real a mencionar en la memoria del proyecto, no un fallo de búsqueda. Sí puedes usar la provincia de Alicante como referencia de contexto, o el IPV (índice de precios de vivienda) del INE para venta, si más adelante retomas esa línea.

### VUT — Registro de Viviendas de Uso Turístico (Generalitat Valenciana)
Consulta completa al portal de datos abiertos de la Generalitat (dadesobertes.gva.es), API CKAN, filtrado por "raspeig": **101 viviendas de uso turístico registradas** en San Vicente del Raspeig a fecha de hoy. Aggregados relevantes:
- Superficie media: 174,0 m²
- Plazas medias: 6,4
- Solo 2 registradas como "rural" y ninguna como "estudio" — el parque VUT del municipio es mayoritariamente vivienda familiar/grande, no estudios pequeños
- Altas por año: crecimiento sostenido desde 2015, con picos en 2023, 2024 y 2025 (~19-21 altas nuevas cada año), lo que indica que el mercado de vivienda turística en el municipio sigue en expansión activa

Fichero: `vut_san_vicente_raspeig.csv` (101 registros + cabecera).

## 2. Alquiler vacacional/turístico — datos de mercado

Cerré el hueco que dejaba el caveat del INE (ver sección 1) sacando precios reales de anuncios activos en Airbnb y Booking específicamente en San Vicente del Raspeig, en vez de depender solo del proxy de Alicante ciudad.

**Airbnb** (`airbnb_san_vicente_raw.csv`, 18 anuncios, estancias de 5 noches): de los 10 anuncios efectivamente ubicados en San Vicente del Raspeig (el resto son de Alicante o Mutxamel, que Airbnb mete en el mismo radio de búsqueda — quedan marcados con la columna `en_san_vicente`), el precio medio para piso/habitación/estudio (excluyendo las dos villas de lujo, que son un producto distinto) sale en torno a **86 €/noche**, con un rango de 34 a 147 €/noche según tamaño y ubicación. Las dos villas con piscina rondan los 480-985 €/noche, muy por encima — conviene tratarlas como categoría aparte en la limpieza.

**Booking** (`booking_san_vicente_raw.csv`, 12 anuncios en San Vicente, estancias de 3 noches): mezcla bastante hoteles/residencias de estudiantes (habitación suelta) con algún piso y villa completos. El comparable más útil es "Mirador Parque" (piso de 3 dormitorios/2 baños): 313€/3 noches ≈ **104 €/noche**, coherente con la cifra de Airbnb.

Ambas fuentes convergen en algo así como **85-105 €/noche para un piso/apartamento estándar** en San Vicente del Raspeig, sensiblemente por debajo del ADR de ~105€ que había usado como proxy de Alicante ciudad (razonable, dado que San Vicente no tiene playa) pero no muy lejos — así que el proxy de Alicante como techo orientativo no estaba mal encaminado, solo algo optimista.

Como contexto adicional (proxy de Alicante, techo orientativo, no cifra de San Vicente): ocupación media ~77% (≈281 noches/año), picos >83% en temporada alta, ROI bruto estimado 6-10% para vacacional bien gestionado (vs. 3,5-5% en alquiler residencial de larga duración).

## 3. Extracción de portales — datos RAW (alquiler)

| Fuente | Fichero | Filas | Notas |
|---|---|---|---|
| Idealista | `idealista_san_vicente_raw.csv` | 90 anuncios | 3 páginas (30/página) del filtro alquiler-viviendas con precio hasta 2.000€, 2-5 hab. Universo total confirmado en el portal: 133 anuncios con ese filtro |
| Fotocasa | `fotocasa_san_vicente_raw.csv` | 26 anuncios | Universo total confirmado: 104 anuncios (Centro 80, Norte 15, resto de zonas 9) |
| UA — Bolsa de Alojamiento | `ua_bolsa_alojamiento_san_vicente_raw.csv` | 45 anuncios | Muestra completa de la zona San Vicente del Raspeig del tablón oficial de la Universidad de Alicante (cvnet.cpd.ua.es/Alojamiento), incluye alquiler de habitación (régimen CO) y piso completo (régimen A), con precio, dirección, régimen, periodo mínimo y observaciones — esta fuente es clave para tu estrategia de "alquiler por habitación a estudiantes" |
| VUT | `vut_san_vicente_raspeig.csv` | 101 registros | Registro oficial GVA, ver sección 1 |

Cada CSV está en formato RAW tal y como se extrajo (separador `;` por el formato de precios en coma española), sin normalizar todavía precio/m²/habitaciones a un esquema común.

## 4. Venta de viviendas — datos RAW (para rentabilidad de compra)

Para poder calcular la rentabilidad de comprar un piso y destinarlo a alquiler (yield bruto = alquiler anual / precio de compra, y ROI neto una vez descontados gastos de compra e hipoteca), extraje también anuncios de venta:

| Fuente | Fichero | Filas | Notas |
|---|---|---|---|
| Idealista (venta) | `idealista_venta_san_vicente_raw.csv` | 90 anuncios | 3 páginas (30/página), sin filtro de precio/habitaciones. Universo total en el portal: 422 anuncios en venta |
| Fotocasa (venta) | `fotocasa_venta_san_vicente_raw.csv` | 20 anuncios | Muestra tras scroll progresivo (carga diferida). Universo total: 395 anuncios en venta. Incluye zona, habitaciones, baños y m² ya separados en columnas |

Con la muestra de Idealista (90 anuncios) el precio medio ronda los **445.500 €** (mín. 99.950€, máx. 1.650.000€ — el máximo corresponde a un chalet de lujo, un outlier a vigilar en la limpieza), con una superficie media de **243 m²** y un precio implícito medio de **~2.288 €/m²**. Esta cifra es sensiblemente más alta que el precio medio de venta citado en la sección 1 (~1.697 €/m², de un agregador distinto) — es esperable, porque esta muestra incluye muchos chalets/villas grandes (Los Girasoles, Villamontes) que suben la media; conviene segmentar piso vs. chalet en la fase de limpieza antes de sacar conclusiones de rentabilidad por tipo de vivienda.

Con estos datos ya puedes cruzar, para un mismo arquetipo de vivienda (mismo barrio, m² y habitaciones), el precio de compra (Idealista/Fotocasa venta) contra el alquiler que generaría en cada una de las cuatro estrategias (Idealista/Fotocasa/UA alquiler para residencial y estudiantil, VUT + proxy Alicante para turístico) y obtener así el ROI de comprar-para-alquilar en cada modelo.

## 6. Gastos y fiscalidad — para pasar de ingresos brutos a netos

Esto cierra el segundo hueco que comentábamos: sin esto no se puede calcular ROI neto, solo yield bruto. Cifras orientativas, todas con fuente:

**Compra (gasto único, no recurrente):**
- ITP (Impuesto de Transmisiones Patrimoniales) en la Comunitat Valenciana: **9%** del precio de compra para vivienda de segunda mano de uso general (baja desde el 10% en junio de 2026). Existen tipos reducidos (6% u 8%, incluso 3-4%) para compradores menores de 35 años en su vivienda habitual, familias numerosas o víctimas de violencia de género, con límites de renta — no aplicable si el destino es alquiler/inversión, solo si es vivienda habitual del comprador.
- Notaría: 0,2-0,5% del precio
- Registro de la Propiedad: 0,10-0,25% del precio
- Gestoría (opcional): 300-500€ fijos
- Total orientativo: **~10-12% del precio de compra** sumando impuesto + gastos, coherente con lo que se suele citar como regla general

**Recurrentes (anuales/mensuales):**
- IBI en San Vicente del Raspeig: tipo impositivo urbano **0,767%** sobre el valor catastral (no el de mercado) — normalmente muy inferior al valor catastral, así que la cuota real suele quedar en el rango de unos pocos cientos de euros/año, pero para una cifra exacta hace falta el valor catastral de cada inmueble concreto
- Comunidad de propietarios: no hay una media oficial única — el rango real observado va de ~50 a ~240 €/mes según si el edificio tiene ascensor, piscina, zonas comunes, etc. Para un piso estándar sin muchos extras, 40-100€/mes es un rango de partida razonable
- Seguro de hogar: gasto habitual pero variable según póliza/contenido, sin cifra única fiable
- Seguro de impago de alquiler (recomendable para residencial/estudiantil): **5-8% de la renta anual bruta** (p. ej. para 900€/mes, 540-864€/año)
- Mantenimiento/reparaciones: sin cifra oficial, se suele estimar como % del alquiler anual (a definir como supuesto propio)

**Específicos de turístico:**
- Comisión de plataforma: Booking cobra de media **~15%** de cada reserva; Airbnb depende del modelo — con el "modelo split fee" (el más habitual hoy) retiene solo **~3%** al anfitrión (el resto lo paga el huésped aparte), o **14-16%** si se usa el modelo "host-only"
- A eso hay que sumar limpieza entre estancias y, si se contrata gestión integral (para no llevarlo tú misma), un % adicional de gestión — no encontré una cifra única fiable para esto último, habría que pedir presupuesto a una gestora de la zona si quieres afinarlo

**Fiscalidad (IRPF, para el propietario particular):**
- Alquiler residencial de larga duración: reducción del **50%** sobre el rendimiento neto como caso general (contratos posteriores a mayo 2023); hasta 60% si la vivienda se ha rehabilitado, 70% si el inquilino tiene 18-35 años en zona tensionada, y 90% si se baja el alquiler ≥5% respecto al inquilino anterior en zona tensionada — San Vicente del Raspeig habría que comprobar si está declarada zona tensionada para aplicar los tramos altos
- Alquiler por habitación (estudiantil): se declara igual que el residencial si es la vivienda habitual del inquilino durante el curso
- Alquiler turístico/vacacional (Airbnb/Booking sin servicios de hostelería): tributa como rendimiento del capital inmobiliario **sin ninguna reducción** — este es un punto clave para tu comparativa de estrategias, porque penaliza fiscalmente al turístico frente al residencial aunque genere más ingresos brutos

## Pendiente / posibles siguientes pasos
- Pasar tus arquetipos de vivienda por la calculadora oficial de SERPAVI para tener el precio de referencia legal de cada comparable.
- Segmentar piso vs. chalet/villa en los datos de venta antes de calcular el ROI de compra, dado el efecto outlier de las viviendas de lujo en el precio medio.
- Confirmar si San Vicente del Raspeig está declarada zona de mercado residencial tensionado (afecta a la reducción IRPF del residencial y por tanto a la comparativa de estrategias).
- Si se quiere afinar comunidad/mantenimiento/gestión turística, lo más fiable sería pedir presupuesto real a una administración de fincas o gestora turística de la zona, ya que no hay cifra oficial única.
- Con todo esto ya recopilado, el siguiente paso es la fase de limpieza y clasificación (deduplicar, quitar outliers de lujo, normalizar precio/m²/habitaciones) antes de construir el modelo financiero comparativo.

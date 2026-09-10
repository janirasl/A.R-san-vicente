# Petición de datos a Inside Airbnb

## Qué se pide y por qué

El proyecto tiene una única debilidad grande: **la ocupación turística real de San Vicente del Raspeig no está medida**. Todo el modelo la trata como supuesto, y el resultado principal (el punto de equilibrio en noches) existe precisamente para no depender de ella.

Inside Airbnb publica, por ciudad, un `calendar.csv` con disponibilidad por fecha y un `reviews.csv` que permite estimar ocupación por tasa de reseñas. Eso convertiría el supuesto en una estimación basada en actividad local.

## Lo que hay que saber antes de escribir

Comprobado en su web (septiembre 2026):

- **Alicante no está cubierta.** En España solo publican Barcelona y Euskadi.
- Se puede pedir una región nueva, pero **las peticiones de región nueva arrancan en 375 $**.
- La financiación depende del perfil: activistas, periodistas y **residentes** con uso alineado a la misión del proyecto normalmente no tienen que financiarla; investigadores e instituciones sí.
- Contacto: `data@insideairbnb.com`

La vía razonable es presentarse como **residente del municipio haciendo un estudio no comercial**, que es exactamente el caso, y preguntar antes de asumir el coste.

**Aviso técnico:** aunque llegara el dataset, la ocupación de Inside Airbnb es **estimada** (tasa de reseñas × estancia media), no reservas reales. Mejora mucho lo que tenemos, pero no es un dato duro. Conviene decirlo así en la memoria.

---

## Borrador del correo (español)

> **Asunto:** Solicitud de datos — San Vicente del Raspeig (Alicante), estudio no comercial
>
> Hola,
>
> Me llamo Janira Sánchez y soy residente en la provincia de Alicante. Estoy realizando un estudio no comercial sobre el impacto de los distintos modelos de alquiler en San Vicente del Raspeig (Alicante, España), un municipio de unos 60.000 habitantes que alberga la Universidad de Alicante.
>
> El objetivo del estudio es comparar la rentabilidad de cuatro modelos de alquiler de una misma vivienda —alquiler residencial de larga duración, alquiler por habitaciones a estudiantes, alquiler turístico y un modelo mixto— para entender qué presión ejerce cada uno sobre el acceso a la vivienda en un municipio universitario.
>
> He podido documentar los precios (tanto de alquiler residencial como turístico) a partir de fuentes públicas, pero **no existe ninguna fuente pública de ocupación turística para este municipio**: el INE solo publica ocupación para municipios declarados "punto turístico", y San Vicente del Raspeig no lo es. Esa ausencia es la principal limitación del trabajo.
>
> Veo que Alicante no figura entre las regiones publicadas actualmente. Mi consulta es si sería posible una petición de datos para el área de Alicante que incluyera San Vicente del Raspeig, en particular `calendar.csv` y `reviews.csv`, y en qué condiciones.
>
> Quedo a su disposición para ampliar cualquier detalle sobre el estudio o su uso previsto. Los resultados serán públicos y no tienen finalidad comercial.
>
> Muchas gracias por el trabajo que hacéis.
>
> Un saludo,
> Janira Sánchez

## Borrador del correo (inglés)

> **Subject:** Data request — San Vicente del Raspeig (Alicante, Spain), non-commercial study
>
> Hello,
>
> My name is Janira Sánchez and I live in the province of Alicante, Spain. I am carrying out a non-commercial study on how different rental models affect housing in San Vicente del Raspeig, a municipality of around 60,000 inhabitants that hosts the University of Alicante.
>
> The study compares the profitability of four rental models applied to the same dwelling — long-term residential, room-by-room student rental, short-term tourist rental, and a mixed model — in order to understand the pressure each one puts on housing access in a university town.
>
> I have been able to document prices for both residential and tourist rentals from public sources, but **there is no public source of tourist occupancy for this municipality**: Spain's national statistics institute only publishes occupancy for municipalities officially designated as "tourist points", and San Vicente del Raspeig is not one of them. That gap is the main limitation of my work.
>
> I can see Alicante is not among the regions currently published. My question is whether a data request covering the Alicante area, including San Vicente del Raspeig, would be possible — specifically `calendar.csv` and `reviews.csv` — and under what conditions.
>
> I am happy to give any further detail about the study or its intended use. The results will be public and have no commercial purpose.
>
> Thank you for the work you do.
>
> Best regards,
> Janira Sánchez

---

## La alternativa gratuita, y probablemente mejor

Antes de pagar nada, merece la pena hacer esto:

**Rastrear el calendario de disponibilidad de los 4-5 pisos comparables de San Vicente durante varias semanas.**

Es la misma señal subyacente y tiene tres ventajas sobre el dataset completo:

1. **Cuesta cero.**
2. **Está mejor dirigida.** Solo nos importan los pisos comparables al arquetipo; un dataset de toda Alicante estaría dominado por apartamentos de playa de la capital, que no son nuestro mercado.
3. **Es un dato observado, no estimado.** Ver qué noches están bloqueadas es más directo que inferir ocupación desde la tasa de reseñas.

Su limitación: una noche bloqueada puede ser una reserva o puede ser que el propietario no quiera alquilar. No se distinguen. Aun así, es un límite superior de disponibilidad y un buen indicador de actividad.

**Recomendación:** escribir a Inside Airbnb (no cuesta nada preguntar, y si entra como uso alineado sería gratis) y en paralelo empezar el rastreo propio, que da resultados sin depender de la respuesta.

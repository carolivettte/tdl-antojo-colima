# Propuesta del Observatorio · Antojo Colima

**Equipo:** Carol Ivette Rodríguez Lepe · Avlix Eduardo Jiménez Cuevas
**Proyecto integrador:** Trusted Data Lab (Ingeniería de Datos · Análisis Estadístico · Calidad en los Sistemas de Información)
**Entrega:** E0 · Arranque · noviembre de 2026

---

## 1. Ficha del observatorio

| Campo | Definición |
|---|---|
| **Nombre** | Observatorio Antojo Colima |
| **Sector** | Servicios de preparación de alimentos y bebidas (SCIAN 722): taquerías, cafeterías, fondas y restaurantes |
| **Región** | Estado de Colima (Colima, Villa de Álvarez, Manzanillo, Tecomán y demás municipios) |
| **Pregunta detonadora** | ¿En qué meses le conviene a una taquería o cafetería de Colima hacer promociones o ajustar precios, según lo que le cuestan sus insumos y lo que hace su competencia? |
| **Cliente potencial** | Taquerías y cafeterías pequeñas y medianas de Colima; personas que quieren abrir un negocio de comida; CANIRAC Colima; Secretaría de Desarrollo Económico del estado |
| **Producto** | Tablero público con el "calendario de temporadas" de insumos, pronóstico de precios y mapa de competencia, más un reporte mensual de inteligencia |
| **Modelo de negocio** | Reporte por suscripción para negocios y asociaciones; convenio institucional con la dependencia estatal o con la cámara del sector |

### ¿Por qué importa?

En Colima la mayoría de los negocios de comida son micro (0 a 5 personas) y deciden precios y promociones "al tanteo". Cuando el limón, el aguacate o el tomate se disparan, el margen se pierde sin aviso. Los datos para anticiparlo ya existen y son públicos (SNIIM e INEGI), pero están dispersos y nadie los traduce a decisiones concretas para un taquero o un dueño de cafetería. Además, la comida fuera de casa es de los rubros que más empujan la inflación: el INEGI reporta de forma recurrente al genérico "loncherías, fondas, torterías y taquerías" entre los de mayor incidencia en el INPC.

---

## 2. Entrevista de campo

| Campo | Dato |
|---|---|
| Fecha | 8 de noviembre de 2026 |
| Duración | 16 minutos transcurridos: 11 minutos de conversación efectiva y 5 minutos de interrupciones por atención a clientes |
| Perfil de la entrevistada | Persona con puesto de supervisión en una cafetería del estado de Colima. Se omiten su nombre y el del establecimiento para preservar el anonimato |
| Entrevistadores | Carol Ivette Rodríguez Lepe y Avlix Eduardo Jiménez Cuevas |

### Preguntas y respuestas

| # | Pregunta | Qué alimenta | Respuesta (resumen) |
|---|---|---|---|
| 1 | ¿Cuáles son los ingredientes que más cuestan? ¿Cuál presenta aumentos repentinos? ¿Dónde y cada cuánto compran? | Selección de insumos y fuentes | Los tres ingredientes señalados son café, leche dorada y carnes frías para sándwiches. Las carnes frías presentan los aumentos más problemáticos. Compran en Sam's Club cada 15 días. |
| 2 | ¿En qué temporadas venden más o menos? ¿Cómo afectan las lluvias y festividades? | Estacionalidad y pronóstico (E1) | Septiembre y octubre son la temporada más baja; la entrevistada lo atribuye al periodo de mediados del semestre escolar. Durante la lluvia disminuye la afluencia, aunque después las ventas suelen compensarse. Al iniciar la feria a finales de octubre disminuye notablemente la afluencia. No se identificaron meses específicos de mayor venta. |
| 3 | ¿Cada cuánto ajustan los precios? ¿Quién decide los aumentos? ¿Han perdido clientes por ello? | Pregunta central | Ajustan precios aproximadamente dos veces al año: a inicios y a mediados de año. Los dueños deciden cuándo y cuánto aumentar. No se profundizó en la pérdida de clientes por aumentos de precios. |
| 4 | ¿Qué promociones ofrecen? ¿Cuáles funcionan mejor? ¿Cómo las anuncian? ¿Aceptarían probar nuevas promociones? | Experimento factorial (E2) | Ofrecen 2x1 en happy hour de 4:00 a 6:00 p. m. y 20 pesos de descuento en frappés los sábados. La promoción más solicitada es happy hour. Se anuncian mediante redes sociales y un cartel afuera del local. Existe posibilidad de probar propuestas del equipo, sujeta a revisión y autorización de los dueños. |
| 5 | ¿Quién es su competencia? ¿Por qué eligieron la ubicación? ¿Usarían un reporte de insumos y competencia y cuánto pagarían? | Competencia (E3) y modelo de negocio | Identifican principalmente a Starbucks como competencia. La entrevistada desconoce por qué los dueños eligieron la ubicación. Sí utilizarían un reporte; el pago dependería de su nivel de detalle. No se estableció un monto. |

### Aprendizajes

1. _Aprendizaje 1 y cómo cambia el plan._
2. _Aprendizaje 2._
3. _Aprendizaje 3._

---

## 3. Las tres preguntas analíticas

### E1 · Variable a pronosticar (series de tiempo)

**Precio frecuente mensual (MXN/kg) de los insumos clave en los Centros de Distribución de Colima**, reportado por el SNIIM, con horizonte de 3 a 6 meses. Productos: limón, aguacate, tomate saladette, tomate verde, cebolla, chiles serrano y jalapeño, cilantro y papa.

- A partir de esos precios se construirá un **Índice de Costo del Taco** (canasta ponderada de insumos, con ponderaciones informadas por la entrevista).
- Serie histórica prevista: datos diarios desde enero de 2018, agregados a frecuencia mensual. La cobertura real se verificará después de la descarga, contando meses con observaciones válidas e identificando meses faltantes. Para E0 se requiere una serie de al menos 36 periodos comparables.
- Modelos a comparar en E1: suavizamiento exponencial simple, Holt, Holt-Winters y ARIMA/SARIMA. Se reservarán los últimos periodos como conjunto de prueba y se compararán MAE, RMSE y MAPE cuando sea aplicable. La selección se justificará con los resultados de validación.
- Pregunta: *¿En qué meses de 2027 se espera que suba o baje el costo de los insumos y, por lo tanto, cuándo conviene hacer promociones?*
- En E1 se integrará como serie de contraste el INPC del genérico "loncherías, fondas, torterías y taquerías" (API del INEGI).

### E2 · Factores a experimentar (diseño factorial)

**Ruta de negocio (preferente, si el negocio entrevistado acepta):** diseño 2³ sobre publicaciones de promociones en redes sociales del negocio.

| Factor | Nivel bajo (−) | Nivel alto (+) |
|---|---|---|
| A · Mensaje | Descuento ("2x1", "-15%") | Combo de valor ("taco + bebida") |
| B · Imagen | Foto del producto | Foto del ambiente o personas |
| C · Horario | Mañana (9 a 11 h) | Tarde (17 a 19 h) |

Respuesta: interacciones (reacciones, comentarios y mensajes) en 24 horas, con réplicas en semanas distintas.

**Ruta de ingeniería (respaldo):** diseño 2³ sobre el extractor del SNIIM. Factores: pausa entre peticiones (1.5 vs 3 s), tamaño del bloque de fechas (31 vs 92 días) y formato de escritura (CSV vs Parquet). Respuestas: tiempo total de captura y tasa de errores. Esta ruta también es evidencia de eficiencia de desempeño para la evaluación ISO/IEC 25010.

### E3 · Grupos multivariados a comparar (PCA y MANOVA)

**Grupos:** municipios de Colima (Colima, Villa de Álvarez, Manzanillo, Tecomán y "resto del estado") y tipos de negocio del DENUE (taquerías, cafeterías, restaurantes a la carta, antojitos y comida para llevar).

**Variables por grupo:** negocios por cada 10 mil habitantes, proporción de micronegocios (0 a 5 personas), distancia media al competidor más cercano, diversidad de giros y concentración en corredores comerciales.

Pregunta: *¿Los municipios de Colima tienen perfiles de competencia distintos al considerar todas las variables a la vez?* PCA para reducir dimensiones y dibujar el mapa de perfiles; MANOVA para probar la diferencia entre grupos, verificando la normalidad multivariada (o usando PERMANOVA si no se cumple).

---

## 4. Plan de recopilación de datos

### 4.1 Fuentes

| # | Fuente | Qué aporta | Estructura y formato | Frecuencia | Método de acceso | Uso |
|---|---|---|---|---|---|---|
| 1 | **SNIIM**, Secretaría de Economía | Precios mínimo, máximo y frecuente por producto, presentación, origen y destino | Tabla HTML; fecha, presentación, origen, destino, precios (texto) | Diaria (días hábiles) | Scraping ético de la consulta pública por fechas | **Captura diaria automática** y serie histórica 2018 a la fecha |
| 2 | **Open-Meteo** (ERA5 y pronóstico) | Temperatura máxima, mínima y media, lluvia y humedad diarias en Colima | JSON (arreglos por variable) | Diaria | API REST sin llave | **Segunda captura diaria automática**; covariable de estacionalidad |
| 3 | **DENUE**, INEGI | Negocios del subsector 722 en Colima: giro, tamaño, ubicación y coordenadas | JSON | Actualización periódica del directorio (fotografía) | API oficial con token gratuito | Grupos y variables de E3 |
| 4 | **Banco de Indicadores**, INEGI (INPC) | Índices de precios de loncherías y taquerías, restaurantes y café; INPC de la ciudad de Colima | JSON | Quincenal y mensual | API oficial con token gratuito | Integración y contraste en E1 |

Todos los datos se guardan en `data/bronce/<fuente>/fecha=AAAA-MM-DD/` tal como llegaron, con un archivo `.meta.json` que registra URL (sin token), fecha y hora UTC de captura, número de registros, columnas, huella SHA-256 y User-Agent. Cada ejecución se anota en `data/bitacora/ejecuciones.csv`.

### 4.2 Análisis ético y legal

| Fuente | robots.txt | Términos de uso | Datos personales | Decisión |
|---|---|---|---|---|
| SNIIM | El extractor lo lee **antes de cada sesión** y se detiene si la ruta está prohibida (`PermissionError`). Se guarda copia fechada en `docs/etica/robots/`. | Información pública del Gobierno de México; se cita la fuente en el tablero y el reporte. | No contiene. | Scraping permitido con User-Agent honesto, pausa ≥ 1.5 s, reintentos con espera exponencial y consultas en bloques trimestrales para no saturar el sitio. |
| Open-Meteo | No aplica (API documentada). Se respeta su límite de uso. | Gratuito para uso no comercial por debajo de 10,000 llamadas diarias; datos bajo CC BY 4.0 con atribución. | No contiene. | 1 o 2 llamadas diarias; atribución visible en el tablero. Si el observatorio se comercializa, se pasa al plan de pago o a otra fuente. |
| DENUE | API oficial; el acceso se autoriza con token personal. | Términos de libre uso de la información del INEGI: se permite usar y redistribuir citando la fuente. | **Sí contiene**: razón social (puede ser el nombre de una persona física), teléfono, correo y sitio web. | Esas 4 columnas **se eliminan antes de guardar** en bronce (prueba automática `test_denue_elimina_datos_personales`). Se conserva solo el nombre comercial, el giro, el tamaño y la ubicación del establecimiento. |
| INEGI Indicadores | API oficial con token. | Términos de libre uso de la información del INEGI. | No contiene. | Uso directo con atribución. |

**Reglas comunes:** el token del INEGI vive solo en el secreto `INEGI_TOKEN` de GitHub y se oculta (`***`) en cualquier metadato o bitácora; ningún dato personal llega al repositorio; si un sitio prohíbe el acceso, se busca otra fuente.

> _Hallazgo de la primera prueba (7 de noviembre de 2026):_ una consulta de prueba al DENUE alrededor del centro de Colima devolvió una razón social con nombre de persona, teléfonos y correos. Se registró como defecto 1 en `calidad/defectos-carol.csv` y motivó la regla de eliminación.

---

## 5. Máquina de captura (capa bronce)
Estado al preparar esta propuesta: captura automática y descarga histórica pendientes de ejecución y verificación. La configuración descrita es la prevista; su funcionamiento y la cobertura real se documentarán con evidencias.

- **Automatización:** `.github/workflows/captura.yml` corre todos los días a las 20:15 (hora de Colima) y guarda datos y bitácora en el repositorio. También se puede lanzar a mano en modo `historico`.
- **Extractor ético:** `extractores/base.py`, basado en el Kit de arranque (robots.txt, `Crawl-delay`, User-Agent con contacto del equipo, pausa mínima y espera exponencial).
- **Tolerancia a fallos:** cada fuente corre por separado; si una falla, las demás continúan y el error queda en la bitácora, que es la base para medir fiabilidad y disponibilidad en E1.
- **Serie histórica prevista:** precios del SNIIM y clima desde 2018-01-01, sujetos a disponibilidad y verificación después de la descarga.

---

## 6. Sistema de calidad inicial

Registros individuales (PSP): `calidad/tiempo-carol.csv`, `calidad/tiempo-avlix.csv`, `calidad/defectos-carol.csv` y `calidad/defectos-avlix.csv`. Los objetivos de calidad medibles están en [`calidad/objetivos.md`](../../calidad/objetivos.md):

1. Tasa de éxito de las ejecuciones de captura programadas ≥ 95%, medida por fuente.
2. Cero secretos expuestos y cero datos personales en el repositorio.
3. Completitud y validez de los registros de precios ≥ 98% (cuarentena ≤ 2%).

---

## 7. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| El SNIIM cambia el formato de su página o bloquea las IP de GitHub Actions | Prueba automática del parser con HTML de ejemplo; la bitácora detecta el fallo el mismo día; respaldo: descarga manual fechada documentada |
| El INPC por genérico no se publica para la ciudad de Colima | Usar el genérico nacional más el INPC general de Colima |
| No se consigue negocio para el experimento de E2 | Ruta de ingeniería sobre el extractor |
| Datos personales en fuentes nuevas (redes sociales en E2) | Eliminación o anonimización en bronce y prueba automática por fuente |

## 8. Roles

| Rol | Integrante | Responde también por |
|---|---|---|
| Data Engineer | Carol Ivette Rodríguez Lepe | Explicar cualquier análisis estadístico |
| Data Statistician | Avlix Eduardo Jiménez Cuevas | Explicar cualquier extractor o regla de limpieza |
| Quality Lead (E0) | Avlix Eduardo Jiménez Cuevas | Revisar el trabajo del compañero con lista de comprobación |

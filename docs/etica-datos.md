# Declaración de ética y legalidad de los datos · Observatorio Antojo Colima

Versión E2 · noviembre de 2026 · Responsables: Carol Ivette Rodríguez Lepe (Data Engineer) y Avlix Eduardo Jiménez Cuevas (Data Statistician, Quality Lead E2).

Este documento declara, fuente por fuente, con qué permiso usamos cada dato, qué dice su `robots.txt`, bajo qué licencia lo redistribuimos, qué datos personales podría traer y cómo los eliminamos, y qué sesgos tiene el observatorio y cómo los mitigamos. Amplía el análisis de E0 ([propuesta §4.2](E0/propuesta.md#42-análisis-ético-y-legal)) con la fuente especializada geoespacial de E2.

---

## 1. Inventario de fuentes

| Fuente | Organismo | Qué usamos | Acceso | Estado |
|---|---|---|---|---|
| SNIIM, Mercados Nacionales | Secretaría de Economía | Precios mínimo, máximo y frecuente de 8 insumos en los Centros de distribución de Colima | Consulta pública por fechas (HTML) | Activa desde E0 |
| DENUE, subsector 722 | INEGI | Negocios de preparación de alimentos (taquerías, fondas, etc.) | API oficial con token | Activa desde E0 |
| **DENUE, afluencia** (E2) | INEGI | Escuelas de todos los niveles (SCIAN 611), consultorios públicos de medicina general (621112), otros centros sin hospitalización (6214) y hospitales (622) | API oficial con token, `BuscarAreaAct` | **Nueva** |
| **Marco Geoestadístico** (E2) | INEGI | Límites de los 10 municipios de Colima (polígonos) | Servicio web `wscatgeo/v2/geo/mgem/06`, sin token | **Nueva** |
| Banco de Indicadores (INPC) | INEGI | Índices de precios para contraste | API oficial con token | Preparada, sin series activas |
| Open-Meteo y NASA POWER | — | Clima | — | **Descartadas** en E0 por `robots.txt` |

---

## 2. Base legal y términos de uso

**INEGI (DENUE, DENUE afluencia, Marco Geoestadístico, Indicadores).** El uso del sitio y de la información se rige por los [Términos de uso del INEGI](https://www.inegi.org.mx/inegi/terminos.html), que remiten a los *Términos de Libre Uso de la Información del INEGI*. Lo que aplicamos de ellos:

| Condición de los términos | Cómo la cumplimos |
|---|---|
| Se pueden hacer y distribuir copias **sin alterar ni suprimir sus metadatos** | El GeoJSON del Marco se guarda en bronce **byte por byte como llegó**, con su bloque `metadatos` ("INEGI. Marco Geoestadístico, diciembre de 2025"; "INEGI. Censo de Población y Vivienda, 2020"), y su SHA-256 en el `.meta.json`. Las dos capturas del 20-nov-2026 dieron el mismo SHA-256 (`a345fd58…`). |
| Dar crédito al INEGI como autor: "Fuente: INEGI, *nombre del producto*" | El tablero y cada tabla de oro geoespacial llevan la columna `fuente`; la pestaña Mapa cita "INEGI, Marco Geoestadístico" y "DENUE". |
| No aparentar que el uso representa una postura oficial del INEGI ni que está avalado por él | El observatorio es un proyecto académico; el índice de zonas es **nuestro**, no del INEGI, y así se dice en el tablero. |

El acceso a la API del DENUE se autoriza con un token personal gratuito. El token vive solo en el secreto `INEGI_TOKEN` de GitHub y en un `.env` local ignorado por git; en cualquier metadato o bitácora se reemplaza por `***` (`extractores/bronce.py::ocultar_token`).

**SNIIM (Secretaría de Economía).** Es información pública del Gobierno de México que se consulta sin registro. La citamos como "Fuente: SNIIM, Secretaría de Economía" y la descargamos con un extractor que respeta `robots.txt` (sección 3).

**Licencia de lo que publicamos.** Los datos derivados (plata y oro) se publican en el repositorio con la misma atribución de origen. No re-licenciamos los datos del INEGI ni del SNIIM: quien los reutilice desde aquí queda sujeto a los términos originales.

---

## 3. Análisis de `robots.txt`

El extractor ético (`extractores/base.py`) **lee `robots.txt` antes de cada sesión**, se detiene con `PermissionError` si la ruta está prohibida, respeta `Crawl-delay`, espera al menos 1.5 s entre peticiones al mismo dominio, reintenta con espera exponencial y se identifica con un User-Agent que incluye contacto. Las copias fechadas están en [`docs/etica/robots/`](etica/robots/) (`python -m scripts.verificar_robots`; en GitHub Actions corre en los modos `historico` y `geo`).

| Dominio | Qué dice | Ruta que usamos | Decisión |
|---|---|---|---|
| `www.economia-sniim.gob.mx` | Prohíbe `/Analisis/`, `/Sicia*`, `/2010/` y archivos `.xls` | `/NUEVO/Consultas/MercadosNacionales/...` (no prohibida) | Permitido |
| `www.inegi.org.mx` | `Allow: /app` y otras; solo prohíbe `/auth/register/` | `/app/api/denue/v1/consulta/...` (permitida) | Permitido para DENUE y DENUE afluencia |
| `gaia.inegi.org.mx` | **No publica `robots.txt`** (HTTP 404 el 20-nov-2026, copia en `docs/etica/robots/inegi-marco-geo_2026-11-20.txt`). Según el estándar de robots.txt (RFC 9309), un 404 significa que no hay restricciones. Aun así, el extractor lo consultó antes de capturar, hizo una sola petición y se rige por los términos de uso del INEGI | `/wscatgeo/v2/geo/mgem/06` | Permitido |
| `api.open-meteo.com`, `archive-api.open-meteo.com` | `Disallow: /` | — | **Descartada** (E0) |
| `power.larc.nasa.gov` | `Disallow: /api/` | — | **Descartada** (E0) |

Regla del proyecto: si un sitio prohíbe la ruta, **no se busca la forma de saltarlo**; se busca otra fuente.

---

## 4. Privacidad

**Marco legal.** La Ley Federal de Protección de Datos Personales en Posesión de los Particulares vigente es la publicada en el DOF el 20 de marzo de 2025 (abrogó la de 2010). Amplía la noción de dato personal a cualquier persona *identificable* directa o indirectamente. Para un directorio de negocios esto importa: en micronegocios, la razón social, el teléfono o la dirección suelen ser los de una persona física.

**Principio que seguimos: minimización.** Solo guardamos lo que el análisis necesita: clave del establecimiento (CLEE), actividad SCIAN, estrato de personal, colonia, código postal, municipio y coordenadas.

| Control | Dónde | Evidencia |
|---|---|---|
| Se eliminan **antes de escribir en bronce**: `Nombre`, `Razon_social`, `Telefono`, `Correo_e`, `Sitio_internet`, `Tipo_vialidad`, `Calle`, `Num_Exterior`, `Num_Interior`, `Edificio`, `EDIFICIO_PISO`, `numero_local`, `Manzana` | `config/fuentes.yaml` (`geo.columnas_eliminadas`) y `extractores/geo.py` | `.meta.json` de cada captura lista `columnas_eliminadas` |
| En la capa de afluencia se elimina **también el nombre**: muchos consultorios privados se llaman como el médico | Igual que arriba | La capa no trae `Nombre` |
| **Puerta de privacidad**: si llega una columna personal a plata, el pipeline se detiene | `pipeline/esquemas.py::verificar_privacidad` | Prueba `tests/test_geo.py::test_privacidad_rechaza_columnas_personales` |
| Consultorios **privados** de medicina general (621111) **no se capturan**: son con frecuencia el consultorio de una persona | `config/fuentes.yaml` (solo 621112, sector público) | Ver sesgo S3 |
| El mapa y `geo_puntos.csv` no llevan nombre ni domicilio: solo CLEE, categoría y coordenada | `pipeline/geo.py`, `tablero/app.py` | Prueba `test_construir_geo_produce_tablas_sin_nombres_y_con_linaje` |
| `scripts/rastrear.py` no muestra columnas personales en pantalla aunque el bronce de E1 las tuviera | `scripts/rastrear.py` | — |
| No se cruza el DENUE con ninguna fuente de personas (redes sociales, padrones) | Diseño | — |

**Riesgo residual.** Un puesto semifijo pequeño queda ubicado por coordenada y CLEE. Esa misma información ya es pública en el DENUE, y el observatorio no la combina con nada que identifique a su dueño. Las taquerías conservan en plata su **nombre comercial** (decisión de E0, necesaria para la competencia), pero ese nombre no aparece en el mapa ni en la capa geoespacial.

---

## 5. Sesgos y mitigación

| # | Sesgo | De dónde viene | Efecto en el observatorio | Mitigación |
|---|---|---|---|---|
| S1 | **El DENUE no registra ambulantes** | La unidad de observación de los Censos Económicos y del DENUE es el establecimiento fijo o semifijo; los carritos, ambulantes y puestos que se arman y desarman cada día no se cuentan. En Colima la informalidad laboral fue de 47.4 % en el 1T-2026 (Data México, Secretaría de Economía). | La competencia real de un taquero está **subcontada**, sobre todo cerca de escuelas y hospitales. | **No inventamos puestos.** Usamos la afluencia (escuelas y centros de salud) como indicador de dónde es probable que haya competencia no registrada u oportunidad. El índice es relativo (alta, media, baja por terciles), no un conteo, y se valida contra los semifijos que sí están registrados: Spearman ρ = 0.40 (p ≈ 5×10⁻¹¹) entre afluencia y taquerías semifijas por celda de 1 km. |
| S2 | **Números pequeños** | Una celda rural con 1 o 2 escuelas y ninguna taquería tiene una razón afluencia/taquería alta solo por azar. | Antes de mitigar, 25 de las 75 celdas "alta" tenían 2 o menos puntos de afluencia y 23 no tenían ninguna taquería. | Las celdas con menos de 3 puntos de afluencia **no se clasifican** (`geo.afluencia_minima: 3`) y se muestran en gris. Después: 48 celdas "alta", con mediana de 6.5 puntos de afluencia, y solo 2 sin taquería. |
| S3 | **Cobertura incompleta de la afluencia** | Una escuela con varios turnos puede ser una sola unidad económica; se excluyen a propósito los consultorios privados (privacidad); el DENUE es una fotografía y se actualiza por ediciones. | La afluencia está subestimada, más en salud privada. | Se declara aquí y en el tablero. La primera captura omitía los consultorios públicos (centros de salud); se agregaron (de 1,213 a 1,235 puntos) y el defecto quedó registrado en el PSP. El índice compara celdas entre sí, así que un subconteo parejo no cambia el orden. |
| S4 | **Precio mayorista, no de menudeo** | El SNIIM reporta precios de la central de abasto, no lo que paga el taquero en el mercado o la tienda. | El nivel del índice no es el costo real del taquero; la tendencia sí es útil. | El tablero habla de "índice" y de variaciones, no de pesos por taco. |
| S5 | **Un solo mercado** | El SNIIM solo publica los Centros de distribución de Colima. | No hay diferencias de precio entre municipios. | El precio se trata como estatal; lo municipal sale solo del DENUE y del Marco. |
| S6 | **Límites y puntos en la frontera** | En 36 de 3,278 puntos (1.1 %), el municipio que declara el DENUE no coincide con el polígono del Marco donde cae la coordenada. | Una taquería en la frontera puede contarse en el municipio vecino. | Para lo espacial manda el Marco; la tasa de coincidencia (98.9 %) se publica en `plata/reporte_geo.json`. |
| S7 | **Unidad de área arbitraria** (problema de la unidad de área modificable) | Las zonas son celdas de 1 km. | Con otro tamaño de celda los terciles cambian. | El tamaño está en configuración (`geo.celda_m`) y el análisis de radio de 1 km se reporta aparte. |
| S8 | **Islas** | El Marco incluye las islas Revillagigedo dentro de municipios de Colima, a más de 700 km del continente (el polígono llega a −114.76° de longitud). | Suman unos 157 km² sin negocios y bajarían las densidades. | Los polígonos se recortan a la caja continental de Colima antes de medir el área (5,782 → 5,625 km²). |

---

## 6. Linaje y rendición de cuentas

Cada fila de oro lleva `archivos_bronce` (el archivo o archivos de `data/bronce` de los que sale) y su fecha de ingesta (`capturado_utc`, o `ingesta_min` e `ingesta_max`). `data/oro/linaje.csv` cataloga cada archivo de bronce con su ruta, el SHA-256 registrado al capturar y el recalculado. `python -m scripts.rastrear <tabla> --donde columna=valor` recorre esa cadena y muestra los registros crudos; `--verificar` falla si algún archivo de bronce se modificó. En la corrida del 20-nov-2026: 4,503 de 4,503 filas de oro trazables y 7 de 7 archivos de bronce íntegros.

---

## 7. Compromisos

1. Si una fuente cambia sus términos o su `robots.txt` para prohibir el acceso, la captura se detiene y la fuente se retira.
2. Ningún dato personal llega al repositorio; la puerta de privacidad lo impide y las pruebas lo verifican en cada cambio.
3. Ningún dato se inventa: lo estimado (meses imputados, índice de zonas) se marca como tal.
4. Las limitaciones de la sección 5 se muestran junto al resultado, no solo en este documento.

---

## Referencias

- INEGI. [Términos de uso del sitio y de la información](https://www.inegi.org.mx/inegi/terminos.html).
- Cámara de Diputados. [Ley Federal de Protección de Datos Personales en Posesión de los Particulares](https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf), DOF 20-03-2025.
- INEGI. Directorio Estadístico Nacional de Unidades Económicas, documento metodológico (unidad de observación: establecimientos fijos y semifijos).
- Secretaría de Economía. [Data México: Colima](https://www.economia.gob.mx/es/profile/geo/6), tasa de informalidad laboral 2026-T1.
- INEGI. Marco Geoestadístico, diciembre de 2025 (servicio `wscatgeo`).

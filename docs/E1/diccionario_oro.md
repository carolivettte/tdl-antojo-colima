# Diccionario de datos · capa oro

Generado automáticamente por `pipeline/oro.py` en cada ejecución del pipeline.

## `dim_insumo.csv`

Jerarquía conceptual de insumos: insumo -> tipo -> canasta.

Filas: **8**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `insumo` | str | Nombre normalizado del insumo en el observatorio. | chile_jalapeno |
| `tipo` | str | Subcategoría: fruta, verdura o chile. | chile |
| `canasta` | str | Categoría: canasta del tipo de negocio al que pertenece (taquera). | taquera |
| `producto_sniim` | str | Nombre original del producto en el SNIIM (resolución de nombres). | Chile Jalapeño - Primera |
| `archivos_bronce` | str | Linaje: archivos de data/bronce de los que sale la fila (separados por ;). | sniim_diario_20261113T215740Z.csv;sniim_diario_20261117T232942Z.csv;sniim_diario_20261120T223919Z.csv;sniim_diario_20261124T163009Z.csv;sniim_diario_20261127T163009Z.csv;sniim_diario_20261128T163002Z.csv;sniim_historico_20261109T080451Z.csv |
| `ingesta_min` | str | Linaje: primera fecha de ingesta (UTC) de los registros de bronce usados. | 2026-11-09T08:04:51Z |
| `ingesta_max` | str | Linaje: última fecha de ingesta (UTC) de los registros de bronce usados. | 2026-11-28T16:30:02Z |

## `dim_municipio.csv`

Jerarquía geográfica municipio -> estado con lo que aporta cada fuente.

Filas: **10**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `municipio_clave` | str | Clave INEGI de 5 dígitos (estado 06 + municipio). | 06001 |
| `municipio` | str | Nombre oficial del municipio. | Armería |
| `estado` | str | Entidad federativa. | Colima |
| `negocios_denue` | str | Negocios de preparación de alimentos registrados en el DENUE. | 358 |
| `mercado_sniim` | str | True si el SNIIM reporta precios de un mercado en ese municipio. | False |
| `archivos_bronce` | str | Linaje: archivos de data/bronce de los que sale la fila (separados por ;). | denue_colima_722_20261109T081242Z.csv |
| `ingesta_min` | str | Linaje: primera fecha de ingesta (UTC) de los registros de bronce usados. | 2026-11-09T08:12:42Z |
| `ingesta_max` | str | Linaje: última fecha de ingesta (UTC) de los registros de bronce usados. | 2026-11-09T08:12:42Z |

## `precios_mensuales.csv`

Precio mensual por insumo en los Centros de distribución de Colima (reducción de diario a mensual).

Filas: **661**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `mes` | str | Mes en formato aaaa-mm. | 2020-01 |
| `insumo` | str | Insumo normalizado (ver dim_insumo). | aguacate |
| `tipo` | str | Subcategoría del insumo. | fruta |
| `canasta` | str | Categoría del insumo. | taquera |
| `precio_mediana` | str | Mediana mensual del precio frecuente (MXN/kg); en meses imputados, interpolación lineal. | 55.0 |
| `precio_promedio` | str | Promedio mensual del precio frecuente (MXN/kg); vacío en meses imputados. | 48.56 |
| `precio_min` | str | Mínimo de los precios mínimos del mes (MXN/kg). | 40.0 |
| `precio_max` | str | Máximo de los precios máximos del mes (MXN/kg). | 55.0 |
| `n_registros` | str | Registros diarios válidos usados en el mes. | 9 |
| `n_atipicos` | str | Registros del mes marcados como atípicos (z robusto > 3.5). | 0 |
| `imputado` | str | True si el mes no tuvo publicación y se rellenó. | False |
| `metodo` | str | observado o interpolacion_lineal. | observado |
| `archivos_bronce` | str | Linaje: archivos de data/bronce de los que sale la fila (separados por ;). | sniim_historico_20261109T080451Z.csv |
| `ingesta_min` | str | Linaje: primera fecha de ingesta (UTC) de los registros de bronce usados. | 2026-11-09T08:04:51Z |
| `ingesta_max` | str | Linaje: última fecha de ingesta (UTC) de los registros de bronce usados. | 2026-11-09T08:04:51Z |

## `indice_costo_taco.csv`

Índice de Costo del Taco: canasta de 8 insumos con pesos iguales, base promedio 2021 = 100.

Filas: **80**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `mes` | str | Mes en formato aaaa-mm. | 2020-04 |
| `indice` | str | Valor del índice (100 = costo promedio de 2021). | 90.85 |
| `variacion_mensual_pct` | str | Cambio porcentual contra el mes anterior. | 12.24 |
| `variacion_anual_pct` | str | Cambio porcentual contra el mismo mes del año anterior. | -3.58 |
| `costo_canasta_kg` | str | Suma de la mediana mensual de los 8 insumos (1 kg de cada uno, MXN). | 205.5 |
| `insumos_imputados` | str | Insumos cuyo precio de ese mes fue imputado. | cebolla |
| `archivos_bronce` | str | Linaje: archivos de data/bronce de los que sale la fila (separados por ;). | sniim_historico_20261109T080451Z.csv |
| `ingesta_min` | str | Linaje: primera fecha de ingesta (UTC) de los registros de bronce usados. | 2026-11-09T08:04:51Z |
| `ingesta_max` | str | Linaje: última fecha de ingesta (UTC) de los registros de bronce usados. | 2026-11-09T08:04:51Z |

## `competencia_municipio.csv`

Negocios de comida por municipio y tipo de negocio (DENUE, sin datos personales).

Filas: **116**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `municipio_clave` | str | Clave INEGI del municipio. | 06001 |
| `municipio` | str | Nombre del municipio. | Armería |
| `tipo_negocio` | str | Tipo de negocio derivado de la clase SCIAN. | taqueria |
| `negocios` | str | Número de establecimientos. | 97 |
| `micro` | str | Establecimientos con 0 a 10 personas. | 97 |
| `semifijos` | str | Establecimientos semifijos (puestos). | 24 |
| `pct_micro` | str | Porcentaje de micronegocios del tipo en el municipio. | 100.0 |
| `pct_del_municipio` | str | Porcentaje que representa el tipo dentro del municipio. | 27.1 |
| `archivos_bronce` | str | Linaje: archivos de data/bronce de los que sale la fila (separados por ;). | denue_colima_722_20261109T081242Z.csv |
| `ingesta_min` | str | Linaje: primera fecha de ingesta (UTC) de los registros de bronce usados. | 2026-11-09T08:12:42Z |
| `ingesta_max` | str | Linaje: última fecha de ingesta (UTC) de los registros de bronce usados. | 2026-11-09T08:12:42Z |

## `geo_municipios.csv`

Indicadores espaciales por municipio: límites del Marco Geoestadístico + puntos del DENUE.

Filas: **10**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `municipio_clave` | str | Clave INEGI del municipio (Marco Geoestadístico). | 06001 |
| `municipio` | str | Nombre del municipio. | Armería |
| `area_km2` | str | Área continental en km², medida en UTM 13N (EPSG:32613). | 419.1 |
| `escuela` | str | Escuelas (SCIAN 611) dentro del polígono. | 47 |
| `salud` | str | Consultorios públicos, centros sin hospitalización y hospitales dentro del polígono. | 7 |
| `taqueria_fija` | str | Taquerías fijas del DENUE dentro del polígono. | 73 |
| `taqueria_semifija` | str | Taquerías semifijas del DENUE dentro del polígono. | 24 |
| `taquerias` | str | Total de taquerías registradas. | 97 |
| `afluencia` | str | Escuelas + salud (generadores de afluencia). | 54 |
| `taquerias_km2` | str | Taquerías por km². | 0.231 |
| `afluencia_km2` | str | Generadores de afluencia por km². | 0.129 |
| `afluencia_por_taqueria` | str | Afluencia por taquería registrada. | 0.56 |
| `pct_semifijas` | str | Porcentaje de taquerías que son semifijas. | 24.7 |
| `fuente` | str | Fuente de origen con su organismo (atribución exigida por los términos del INEGI). | DENUE (taquerías y afluencia) + Marco Geoestadístico |
| `archivos_bronce` | str | Linaje: archivos de data/bronce de los que sale la fila (separados por ;). | denue_afluencia_colima_20261120T144104Z.csv;denue_colima_722_20261109T081242Z.csv;mgem_colima_20261120T144105Z.geojson |
| `capturado_utc` | str | Linaje: fecha y hora UTC de ingesta del archivo de bronce. | 2026-11-20 14:41:05.715 |

## `geo_zonas.csv`

Cuadrícula de 1 km: afluencia contra competencia registrada (índice relativo, no conteo).

Filas: **254**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `celda` | str | Identificador de la celda (columna_fila en km de UTM 13N). | 562_2114 |
| `municipio_clave` | str | Municipio donde cae el centro de la celda. | 06007 |
| `latitud` | str | Latitud del centro de la celda (WGS84). | 19.12261 |
| `longitud` | str | Longitud del centro de la celda (WGS84). | -104.40575 |
| `escuela` | str | Escuelas en la celda. | 4 |
| `salud` | str | Centros de salud y hospitales en la celda. | 0 |
| `afluencia` | str | Escuelas + salud. | 4 |
| `taqueria_fija` | str | Taquerías fijas en la celda. | 1 |
| `taqueria_semifija` | str | Taquerías semifijas en la celda. | 0 |
| `taquerias_registradas` | str | Fijas + semifijas. | 1 |
| `presion_demanda` | str | afluencia / (taquerías registradas + 1). | 2.0 |
| `categoria_zona` | str | alta, media o baja por terciles; afluencia insuficiente si hay menos de 3 puntos. | alta |
| `fuente` | str | Fuente de origen con su organismo (atribución exigida por los términos del INEGI). | DENUE (taquerías y afluencia) |
| `archivos_bronce` | str | Linaje: archivos de data/bronce de los que sale la fila (separados por ;). | denue_afluencia_colima_20261120T144104Z.csv;denue_colima_722_20261109T081242Z.csv;mgem_colima_20261120T144105Z.geojson |
| `capturado_utc` | str | Linaje: fecha y hora UTC de ingesta del archivo de bronce. | 2026-11-20 14:41:04+00:00 |

## `geo_puntos.csv`

Puntos para el mapa, sin nombres ni domicilios.

Filas: **3,278**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `clee` | str | Clave única del establecimiento en el DENUE. | 06007722514005991000000000U1 |
| `categoria` | str | taqueria_fija, taqueria_semifija, escuela o salud. | taqueria_fija |
| `municipio_clave` | str | Municipio que declara el DENUE. | 06007 |
| `latitud` | str | Latitud (WGS84). | 19.12192543 |
| `longitud` | str | Longitud (WGS84). | -104.35180535 |
| `capturado_utc` | str | Linaje: fecha y hora UTC de ingesta del archivo de bronce. | 2026-11-09 08:12:42+00:00 |
| `municipio_clave_marco` | str | Municipio donde cae el punto según el Marco Geoestadístico. | 06007 |
| `municipio_marco` | str | Nombre de ese municipio. | Manzanillo |
| `fuente` | str | Fuente de origen con su organismo (atribución exigida por los términos del INEGI). | DENUE preparación de alimentos |
| `archivos_bronce` | str | Linaje: archivos de data/bronce de los que sale la fila (separados por ;). | denue_colima_722_20261109T081242Z.csv;mgem_colima_20261120T144105Z.geojson |

## `linaje.csv`

Catálogo de linaje: cada archivo de bronce que alimenta cada tabla de oro.

Filas: **46**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `tabla_oro` | str | Tabla de oro. | comparacion_modelos |
| `fuente` | str | Fuente del archivo de bronce. | sniim |
| `archivo_bronce` | str | Nombre del archivo de bronce. | sniim_diario_20261113T215740Z.csv |
| `ruta_bronce` | str | Ruta en el repositorio. | data/bronce/sniim/fecha=2026-11-13/sniim_diario_20261113T215740Z.csv |
| `capturado_utc` | str | Fecha y hora UTC de ingesta. | 2026-11-13T21:57:40.536907+00:00 |
| `registros_bronce` | str | Registros del archivo al capturarlo. | 24 |
| `sha256_registrado` | str | SHA-256 guardado en el .meta.json al capturar. | 268a702e70c238261055ad4ec0208a6053e344cb744ac9070c09c5d57bd982b6 |
| `sha256_actual` | str | SHA-256 recalculado en esta corrida. | 268a702e70c238261055ad4ec0208a6053e344cb744ac9070c09c5d57bd982b6 |
| `integro` | str | True si ambos SHA-256 coinciden. | True |

## `pronostico.csv`

Serie observada y pronóstico del Índice de Costo del Taco (ver contrato abajo).

Filas: **83**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `mes` | str | Mes aaaa-mm. | 2020-04 |
| `valor` | str | Índice observado o pronosticado. | 90.85 |
| `tipo` | str | observado o pronostico. | observado |
| `li_95` | str | Límite inferior del intervalo de 95 %. | 132.33 |
| `ls_95` | str | Límite superior del intervalo de 95 %. | 177.03 |
| `modelo` | str | Modelo elegido. | ARIMA |
| `derivado_de` | str | Linaje: tabla de oro de la que se deriva (hereda su archivos_bronce). | indice_costo_taco |

## `comparacion_modelos.csv`

Errores de cada modelo en los 12 meses de prueba.

Filas: **4**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `modelo` | str | SES, Holt, Holt-Winters o ARIMA. | ARIMA |
| `mae` | str | Error absoluto medio. | 12.023 |
| `rmse` | str | Raíz del error cuadrático medio. | 13.991 |
| `mape` | str | Error porcentual absoluto medio. | 9.38 |
| `aic` | str | Criterio de información de Akaike. | 511.165 |
| `detalle` | str | Orden del ARIMA. | orden (2, 1, 0) |
| `elegido` | str | True en el de menor RMSE. | True |
| `derivado_de` | str | Linaje: tabla de oro de la que se deriva. | indice_costo_taco |

## Contrato del pronóstico (lo escribe el cuaderno de pronóstico, lo lee el tablero)

`pronostico.csv`: serie objetivo `indice_costo_taco.indice`.

| Columna | Tipo | Descripción |
|---|---|---|
| `mes` | texto aaaa-mm | Mes. |
| `valor` | float | Índice observado o pronosticado. |
| `tipo` | texto | `observado` o `pronostico`. |
| `li_95` | float | Límite inferior del intervalo de 95% (vacío en observados). |
| `ls_95` | float | Límite superior del intervalo de 95% (vacío en observados). |
| `modelo` | texto | Modelo elegido (SES, Holt, Holt-Winters o ARIMA). |

`comparacion_modelos.csv`: una fila por modelo con `modelo`, `mae`, `rmse`, `mape` (sobre los 12 meses de prueba), `aic`, `detalle` (orden del ARIMA) y `elegido` (True en el de menor RMSE). Los escribe `pipeline/pronostico.py`.

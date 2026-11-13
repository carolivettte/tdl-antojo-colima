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

## `dim_municipio.csv`

Jerarquía geográfica municipio -> estado con lo que aporta cada fuente.

Filas: **10**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `municipio_clave` | str | Clave INEGI de 5 dígitos (estado 06 + municipio). | 06001 |
| `municipio` | str | Nombre oficial del municipio. | Armería |
| `estado` | str | Entidad federativa. | Colima |
| `negocios_denue` | int64 | Negocios de preparación de alimentos registrados en el DENUE. | 358 |
| `mercado_sniim` | bool | True si el SNIIM reporta precios de un mercado en ese municipio. | False |

## `precios_mensuales.csv`

Precio mensual por insumo en los Centros de distribución de Colima (reducción de diario a mensual).

Filas: **661**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `mes` | str | Mes en formato aaaa-mm. | 2020-01 |
| `insumo` | str | Insumo normalizado (ver dim_insumo). | aguacate |
| `tipo` | str | Subcategoría del insumo. | fruta |
| `canasta` | str | Categoría del insumo. | taquera |
| `precio_mediana` | float64 | Mediana mensual del precio frecuente (MXN/kg); en meses imputados, interpolación lineal. | 55.0 |
| `precio_promedio` | float64 | Promedio mensual del precio frecuente (MXN/kg); vacío en meses imputados. | 48.56 |
| `precio_min` | float64 | Mínimo de los precios mínimos del mes (MXN/kg). | 40.0 |
| `precio_max` | float64 | Máximo de los precios máximos del mes (MXN/kg). | 55.0 |
| `n_registros` | int64 | Registros diarios válidos usados en el mes. | 9 |
| `n_atipicos` | int64 | Registros del mes marcados como atípicos (z robusto > 3.5). | 0 |
| `imputado` | bool | True si el mes no tuvo publicación y se rellenó. | False |
| `metodo` | str | observado o interpolacion_lineal. | observado |

## `indice_costo_taco.csv`

Índice de Costo del Taco: canasta de 8 insumos con pesos iguales, base promedio 2021 = 100.

Filas: **80**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `mes` | str | Mes en formato aaaa-mm. | 2020-04 |
| `indice` | float64 | Valor del índice (100 = costo promedio de 2021). | 90.85 |
| `variacion_mensual_pct` | float64 | Cambio porcentual contra el mes anterior. | 12.24 |
| `variacion_anual_pct` | float64 | Cambio porcentual contra el mismo mes del año anterior. | -3.58 |
| `costo_canasta_kg` | float64 | Suma de la mediana mensual de los 8 insumos (1 kg de cada uno, MXN). | 205.5 |
| `insumos_imputados` | str | Insumos cuyo precio de ese mes fue imputado. |  |

## `competencia_municipio.csv`

Negocios de comida por municipio y tipo de negocio (DENUE, sin datos personales).

Filas: **116**

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `municipio_clave` | str | Clave INEGI del municipio. | 06001 |
| `municipio` | str | Nombre del municipio. | Armería |
| `tipo_negocio` | str | Tipo de negocio derivado de la clase SCIAN. | taqueria |
| `negocios` | int64 | Número de establecimientos. | 97 |
| `micro` | int64 | Establecimientos con 0 a 10 personas. | 97 |
| `semifijos` | int64 | Establecimientos semifijos (puestos). | 24 |
| `pct_micro` | float64 | Porcentaje de micronegocios del tipo en el municipio. | 100.0 |
| `pct_del_municipio` | float64 | Porcentaje que representa el tipo dentro del municipio. | 27.1 |

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

`comparacion_modelos.csv`: una fila por modelo con `modelo`, `mae`, `rmse`, `mape` (sobre el conjunto de prueba) y `elegido` (True en el de menor error).

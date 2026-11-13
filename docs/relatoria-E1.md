# Relatoría E1 · Datos de confianza y pronóstico

Carol Ivette Rodríguez Lepe · Avlix Eduardo Jiménez Cuevas · 11 al 13 de noviembre de 2026

## 1. ¿Qué nos propusimos?

Que cada captura viaje sola de bronce a oro con una puerta de calidad que rechace con motivo, publicar en el tablero el pronóstico del **Índice de Costo del Taco** elegido por su error de prueba, y medir la disponibilidad real de la captura contra el objetivo de E0 (≥ 95 %).

## 2. ¿Qué hicimos?

| Fecha | Quién | Qué | Tiempo |
|---|---|---|---|
| 11 nov | Carol | Plan de E1 contra la rúbrica y reparto | 40 min |
| 11 nov | Carol | Revisión de la puerta (Pandera), plata, oro, CI, respaldo, fiabilidad y tablero | 40 min |
| 12 nov | Carol | Revisión sobre el repositorio actualizado; copia limpia, pruebas en Windows (defecto 18) y 8 commits | 55 min |
| 12 nov | Avlix | Revisión de instrucciones y material E1; planificación de la integración | 105 min (21:00–22:45) |
| 13 nov | Avlix | Incorporación del paquete; instalación de dependencias; ejecución del pipeline; 23 pruebas con 90 % de cobertura; Ruff y preparación de commits | 130 min efectivos (00:00–02:25; 15 min de interrupción) |
| 13 nov | Los dos | Publicación del tablero, ajustes finales del tablero, fiabilidad final y etiqueta e1 | 116 min |

Detalle: [tiempo-carol.csv](../calidad/tiempo-carol.csv) · [tiempo-avlix.csv](../calidad/tiempo-avlix.csv). El código se escribió con apoyo de un asistente de IA (declarado en la ficha); la revisión, las pruebas locales y las decisiones fueron del equipo.

## 3. ¿Qué decidimos y por qué?

1. **Marcar los atípicos, no borrarlos.** Descartamos el IQR global porque marcaba la temporada alta de 2022 completa del aguacate: un periodo de escasez real, que es justo lo que le importa al taquero. Usamos el z robusto contra los 120 días anteriores, y a cuarentena solo va lo imposible (mínimo > máximo): 3 de 5,141 registros evaluados.
2. **Interpolar los meses sin publicación.** Ocultamos meses conocidos y probamos 4 métodos: la interpolación lineal se equivocó 10 %, contra 13 a 24 % del arrastre, la media y la spline. Cada mes imputado queda marcado.
3. **Elegir el modelo por RMSE fuera de muestra, no por complejidad.** Holt-Winters, el más complejo, fue el peor (RMSE 15.0) porque la serie casi no tiene estacionalidad (fuerza 0.00). Ganó ARIMA(2,1,0), con RMSE 10.7 y MAPE 7.8 %.

## 4. ¿Qué salió mal y cómo lo corregimos?

* **El `schedule` de GitHub no corrió el 9 de noviembre** ([incidente I2](../calidad/incidentes.csv), defecto Carol 14): costó 5.3 h de reparación y es la única falla de disponibilidad. Lo resolvió un disparador externo (cron-job.org).
* **El respaldo fallaba en Windows** (Carol 18): git cambiaba los saltos de línea de bronce y las huellas SHA-256 no coincidían. Se corrigió con `.gitattributes` para que los datos nunca se conviertan.
* **Los atípicos no se marcaban cuando el precio no se movía** (Carol 16, MAD = 0); lo encontró una prueba automática.
* **Escribimos la interpretación de faltantes y del PCA antes de ver los datos** (Avlix 6). Los datos dijeron otra cosa: el hueco de la cebolla de 2021–2022 es probablemente MNAR (precios 51 % y 106 % arriba de lo normal en sus bordes) y PC1 solo explica 37 %. Se reescribió con las cifras reales.
* **No alcanzamos 7 días de bitácora.** La captura empezó el 9 de noviembre y la rúbrica pide del 6 al 13. Medimos lo que hay (5 días): 80 % de días exitosos, 93.8 % de ejecuciones exitosas y A = 95.3 %, que ya alcanza el objetivo de E0 ([fiabilidad.md](../calidad/fiabilidad.md)).

## 5. ¿Qué aprendimos de cada materia?

**Ingeniería de Datos.** Una puerta solo es confiable si cuadra: bronce (5,253) = plata (5,138) + cuarentena (3) + duplicados resueltos (112), al corte del 13 de noviembre. Si un registro no aparece en ninguno de los tres, se borró en silencio. Reconstruir plata y oro desde bronce en cada corrida resultó más simple y seguro que actualizarlos por partes.

**Análisis Estadístico.** El mismo insumo tuvo un faltante MAR (cebolla 2020, con toda la canasta) y uno probablemente MNAR (2021–2022), y eso solo se vio mirando los precios en los bordes de cada hueco, porque el valor p (0.15) no alcanzaba con 4 puntos. También aprendimos que la descomposición aditiva se justifica con datos: la amplitud no crece con el nivel (correlación −0.73).

**Calidad.** La disponibilidad se calcula con la bitácora, no se declara. Con 5 días medidos, una sola falla deja la tasa diaria en 80 % aunque la disponibilidad (95.3 %) ya cumple el objetivo. Las pruebas encontraron defectos reales (Carol 16 y 18, Avlix 7) antes de que llegaran a `main`.

## 6. Evidencias

* Ficha: [docs/E1/ENTREGA.md](E1/ENTREGA.md) · Commits: `carol/e1-datos` y `avlix/e1-analisis` (PR en GitHub)
* Puerta: [reporte_puerta.json](../data/plata/reporte_puerta.json) · [cuarentena](../data/cuarentena/) · [puerta_calidad.csv](../data/bitacora/puerta_calidad.csv)
* Cuadernos: [E1_limpieza.ipynb](../laboratorio/E1_limpieza.ipynb) · [E1_pronostico.ipynb](../laboratorio/E1_pronostico.ipynb)
* Pronóstico: [pronostico.csv](../data/oro/pronostico.csv) · [comparacion_modelos.csv](../data/oro/comparacion_modelos.csv) · tablero (enlace en la ficha)
* Calidad: [fiabilidad.md](../calidad/fiabilidad.md) · [plan_sqa.md](../calidad/plan_sqa.md) · [requerimientos.md](E1/requerimientos.md) · [defectos-carol.csv](../calidad/defectos-carol.csv) · [defectos-avlix.csv](../calidad/defectos-avlix.csv)

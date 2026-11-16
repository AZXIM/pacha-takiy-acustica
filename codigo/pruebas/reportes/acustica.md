# Reporte acústico de Pacha Takiy

Generado por `scripts/sonic_visualiser.py` el 2026-11-15. No editar a mano.

Comprueba con números que lo que suena es lo que dice la regla del equipo. Las constantes se leen de `web/js/reglas.js` y `web/js/audio.js`; si alguien las cambia, este reporte y `pruebas/python/test_acustica.py` lo detectan.

## 1. El modelo

| Elemento | Fórmula (igual que la Web Audio API) |
|---|---|
| Golpe | seno de 440 Hz · g(t); g sube exponencial de 0.0001 a 0.5 en 5 ms y baja exponencial a 0.0001 en 85 ms |
| Instante del golpe i | t₀ + i · 1.5/n, con n = 2, 4 o 7 golpes |
| Rumor | ruido uniforme [−1, 1] → pasabanda biquad (fc = 1200 Hz, Q = 0.7) → nivel(c) |
| nivel(c) | 0.03 + 0.22 · min(1, c / 0.4) |
| RMS del rumor | nivel · volumen · (1/√3) · √G, con G = (1/π)∫\|H(e^jω)\|² dω = 0.1005 |
| Sonoridad | ley de Stevens: se percibe el doble cada 10 dB |

## 2. ¿Suena lo que dice la regla?

### Episodio del 10/02/2025 (paso 5, tal como suena en la web)

| Momento | Clase | Cobertura | Golpes (regla / medidos) | Error máx. | Rumor previsto | Rumor medido | Golpe sobre rumor* | ¿Cumple? |
|---|---|---|---|---|---|---|---|---|
| 13:30 | baja | 25,4 % | 2 / 2 | 1,4 ms | -32,09 dBFS | -32,23 dBFS | 42,1 dB | sí |
| 14:00 | baja | 24,6 % | 2 / 2 | 1,4 ms | -32,32 dBFS | -32,46 dBFS | 42,3 dB | sí |
| 14:30 | baja | 21,9 % | 2 / 2 | 1,4 ms | -33,14 dBFS | -33,28 dBFS | 43,1 dB | sí |
| 15:00 | baja | 12,1 % | 2 / 2 | 1,4 ms | -37,01 dBFS | -37,15 dBFS | 47,0 dB | sí |
| 15:30 | baja | 14,9 % | 2 / 2 | 1,4 ms | -35,69 dBFS | -35,82 dBFS | 45,7 dB | sí |
| 16:00 | baja | 15,3 % | 2 / 2 | 1,4 ms | -35,55 dBFS | -35,68 dBFS | 45,5 dB | sí |

\* Margen del golpe de 440 Hz sobre el ruido del rumor dentro de la banda crítica del oído (ERB = 24,7·(4,37·f/1000 + 1) ≈ 72 Hz). Más de 10 dB: el rumor nunca tapa un golpe.

### Las tres intensidades (con el volumen al máximo)

| Momento | Clase | Cobertura | Golpes (regla / medidos) | Error máx. | Rumor previsto | Rumor medido | Golpe sobre rumor* | ¿Cumple? |
|---|---|---|---|---|---|---|---|---|
| Baja | baja | 20,0 % | 2 / 2 | 1,5 ms | -31,83 dBFS | -31,96 dBFS | 43,8 dB | sí |
| Media | media | 20,0 % | 4 / 4 | 1,5 ms | -31,83 dBFS | -31,98 dBFS | 43,8 dB | sí |
| Alta | alta | 20,0 % | 7 / 7 | 1,9 ms | -31,83 dBFS | -31,87 dBFS | 43,8 dB | sí |

\* Margen del golpe de 440 Hz sobre el ruido del rumor dentro de la banda crítica del oído (ERB = 24,7·(4,37·f/1000 + 1) ≈ 72 Hz). Más de 10 dB: el rumor nunca tapa un golpe.

## 3. ¿Se puede oír la diferencia entre A y B?

Demostración (`?demo`): A = 13:30 (25,4 %) y B = 15:00 (12,1 %).

- Diferencia de nivel del rumor: **4,92 dB** (umbral de percepción ≈ 1,0 dB; cómodo ≥ 2,0 dB).
- Se percibe **1,41 veces** más fuerte. Veredicto: **se oye con claridad**.
- ¿La respuesta correcta es robusta? Diferencia de cobertura A − B = 13,3 puntos; intervalo de confianza del 95 % por bootstrap de las 100 celdas: **5,0 a 21,9 puntos**. No incluye 0 y su mínimo supera los 3 puntos de `DIF_MIN_COBERTURA`.

### Resolución de la cobertura

La app considera que A y B son distintos si difieren en 3 puntos o más (`DIF_MIN_COBERTURA`). La tabla dice cuánto sube el rumor con esos 3 puntos y cuántos puntos hacen falta para llegar a 1 dB.

| Cobertura | +3 puntos suben (curva actual) | Puntos para 1 dB (actual) | +3 puntos suben (curva en dB, propuesta) | Puntos para 1 dB (propuesta) |
|---|---|---|---|---|
| 5,0 % | 2,19 dB | 1,3 | 1,38 dB | 2,2 |
| 10,0 % | 1,54 dB | 1,9 | 1,38 dB | 2,2 |
| 15,0 % | 1,19 dB | 2,5 | 1,38 dB | 2,2 |
| 20,0 % | 0,97 dB | 3,2 | 1,38 dB | 2,2 |
| 25,0 % | 0,82 dB | 3,8 | 1,38 dB | 2,2 |
| 30,0 % | 0,71 dB | 4,4 | 1,38 dB | 2,2 |
| 35,0 % | 0,62 dB | 5,0 | 1,38 dB | 2,2 |

## 4. Hallazgos y propuestas

Lo que cumple:

- Cada momento tiene exactamente los golpes de la regla (2, 4 o 7), con error de tiempo de 1,9 ms como máximo.
- El rumor nunca tapa los golpes: el margen en la banda crítica es de 42 dB o más.
- Con el volumen al máximo, el pico queda por debajo del umbral del limitador (−3 dBFS): el limitador no cambia el sonido en régimen estable.
- La demostración A/B se oye con claridad (4,9 dB).

Lo que conviene decidir en equipo (no se cambió nada de la regla):

1. **3 puntos de cobertura no siempre se oyen.** Con la curva actual (lineal en amplitud), por encima de ~19,2 % de cobertura 3 puntos suben el rumor menos de 1 dB, que es el límite de lo que el oído distingue. Hoy no afecta a la demo (A y B se eligen en los extremos), pero sí a otros episodios. Propuesta: `nivel(c) = 0,03 · (0,25/0,03)^min(1, c/0,4)` (mismo mínimo y mismo máximo, curva en decibeles): cada punto vale lo mismo, unos 0,46 dB, así que 3 puntos dan ≈1,4 dB en cualquier cobertura. Otra opción es decidir "igual" por dB (|ΔL| < 1 dB) y no por puntos.
2. **El primer sonido tras crear el audio suena ~1,4 dB más bajo.** El limitador del navegador (DynamicsCompressor) tarda ~0,5 s en estabilizarse después de crearse el AudioContext. Solo afecta al primer golpe que se oye al entrar; si es "Escuchar A", A empieza un poco más bajo. Propuesta de una línea en `cambiarModo()` (`web/js/ajustes.js`): `if (modo !== "ver") Motor.asegurar();`. Elegir el modo ya es un gesto, así que el navegador lo permite. Así el limitador lleva más de 0,5 s estable cuando suena el primer momento, y no cambian los tiempos ni la vibración. En la prueba controlada, un golpe que suena 0,5 s o más después de crear el audio sale con 0,0 dB de diferencia.
3. **El rumor va 24 a 29 dB por debajo del pico de los golpes.** En una sala con ruido puede perderse justo la pista que decide A/B. Sugerencia: recomendar audífonos en el paso 3 o un botón "escuchar solo el rumor".

## 5. Comparación con el audio real de la web

Capturado con `pruebas/web/acustica.spec.js`: el Motor real (`web/js/audio.js`, sin cambios) se renderiza con OfflineAudioContext, incluido el limitador.

- Retardo fijo del limitador: **8,1 ms** (constante; la vibración sigue sincronizada).
- Diferencia máxima de nivel del rumor web − modelo: **0,17 dB**.
- Golpes contados en la web: **9 de 9 momentos** con el número exacto.
- Primer golpe tras crear el audio, comparado con el modelo: **-1,4 dB** en promedio (0 dB sería lo ideal; ver hallazgo 2).

### Audio capturado de la web

| Momento | Clase | Cobertura | Golpes (regla / medidos) | Error máx. | Rumor previsto | Rumor medido | Golpe sobre rumor* | ¿Cumple? |
|---|---|---|---|---|---|---|---|---|
| 13:30 | baja | 25,4 % | 2 / 2 | 0,3 ms | -32,09 dBFS | -32,02 dBFS | 42,1 dB | sí |
| 14:00 | baja | 24,6 % | 2 / 2 | 0,2 ms | -32,32 dBFS | -32,41 dBFS | 42,3 dB | sí |
| 14:30 | baja | 21,9 % | 2 / 2 | 0,2 ms | -33,14 dBFS | -32,97 dBFS | 43,1 dB | sí |
| 15:00 | baja | 12,1 % | 2 / 2 | 0,2 ms | -37,01 dBFS | -36,88 dBFS | 47,0 dB | sí |
| 15:30 | baja | 14,9 % | 2 / 2 | 0,3 ms | -35,69 dBFS | -35,65 dBFS | 45,7 dB | sí |
| 16:00 | baja | 15,3 % | 2 / 2 | 0,2 ms | -35,55 dBFS | -35,43 dBFS | 45,5 dB | sí |
| Baja | baja | 20,0 % | 2 / 2 | 0,2 ms | -33,76 dBFS | -33,66 dBFS | 43,8 dB | sí |
| Media | media | 20,0 % | 4 / 4 | 0,4 ms | -33,76 dBFS | -33,86 dBFS | 43,8 dB | sí |
| Alta | alta | 20,0 % | 7 / 7 | 0,7 ms | -33,76 dBFS | -33,59 dBFS | 43,8 dB | sí |

\* Margen del golpe de 440 Hz sobre el ruido del rumor dentro de la banda crítica del oído (ERB = 24,7·(4,37·f/1000 + 1) ≈ 72 Hz). Más de 10 dB: el rumor nunca tapa un golpe.

## Cómo verlo en Sonic Visualiser

Ejecuta `sonic_visualiser.bat` (o `python scripts/sonic_visualiser.py`) y sigue `salidas/sonic_visualiser/LEEME.md`.

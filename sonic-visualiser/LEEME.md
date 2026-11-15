# Escuchar y ver Pacha Takiy en Sonic Visualiser

Sonic Visualiser es gratis: https://www.sonicvisualiser.org/download.html
Para contar golpes automáticamente, instala también el paquete de plugins Vamp de Queen Mary:
https://vamp-plugins.org/plugin-doc/qm-vamp-plugins.html

## Lo más fácil: doble clic en una sesión

Abre **`ab_demo.sv`**, **`tarde.sv`**, **`clases.sv`** o **`temporadas.sv`** (El Niño). Cada sesión carga el audio con su espectrograma,
los golpes marcados, los momentos o temporadas como regiones con su valor, la curva del rumor y, en El Niño, la curva del ONI.
Deja cada `.sv` en la misma carpeta que su `.wav`.

## Abrir un audio con sus capas (a mano)

1. **Archivo → Abrir** y elige `tarde.wav` (o `ab_demo.wav`, `clases.wav`).
2. **Capa → Añadir espectrograma** (Layer → Add Spectrogram). En sus propiedades usa escala de frecuencia **Log**
   y ventana de 1024. Verás una raya a 440 Hz por cada golpe y una mancha difusa alrededor de 1200 Hz: el rumor.
3. **Archivo → Importar capa de anotaciones** (File → Import Annotation Layer):
   - `*_golpes.csv` → elige "Tiempo, Etiqueta": aparece un marcador por golpe.
   - `*_momentos.csv` → columnas "Tiempo, Valor, Duración, Etiqueta": una región por momento; el valor es la cobertura en %.
   - `*_rumor.csv` → "Tiempo, Valor": la curva del nivel previsto del rumor en dBFS.

## Comprobar que el sonido es el dato (sin confiar en el oído)

- **Golpes:** Transformación → Analysis → *Note Onset Detector* (Queen Mary). Sus marcas deben caer encima de las de
  `*_golpes.csv` (diferencia de pocos milisegundos). Si sobra o falta una, la regla no se está cumpliendo.
- **Rumor:** Transformación → Analysis → *Power* o *RMS*. Su curva debe subir y bajar igual que `*_rumor.csv`.
- **A y B:** en `ab_demo.wav`, el momento A debe verse con más rumor que B: más cobertura, más energía alrededor de 1200 Hz.

## El Niño: 44 temporadas de lluvia en Moquegua (`temporadas.wav`)

Una temporada (diciembre a marzo) por momento, de 1981-82 a 2024-25, y al final lo esperado para 2026-27.
Datos: NASA POWER (lluvia de la cuenca alta) y NOAA (índice ONI de El Niño).

- **Golpes = tercil** de la normal 1991–2020: 2 = bajo lo normal, 4 = normal, 7 = sobre lo normal.
- **Rumor = lluvia** de la temporada: más fuerte, más lluvia.
- Importa `temporadas_momentos.csv` (regiones: valor = mm/día y etiqueta = año · fase de El Niño · tercil),
  `temporadas_golpes.csv` (instantes) y `temporadas_oni.csv` como capa **Tiempo, Valor**: la curva del ONI
  sube en cada El Niño. En el espectrograma se ve cómo esos años suenan con menos golpes y menos rumor.

Todo esto lo hace también `python scripts/sonic_visualiser.py` de forma automática y lo escribe en
`pruebas/reportes/acustica.md`.

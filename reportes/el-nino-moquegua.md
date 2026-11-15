# El Niño y la lluvia de Moquegua (calibración con datos de NASA)

Generado por `scripts/enso_moquegua.py`. No editar a mano.

## Datos

- Lluvia: NASA POWER v2.10, API mensual (MERRA-2), parámetro PRECTOTCORR (mm/día). Celda MERRA-2 de la cuenca alta (lat -17.25 a -16.75, lon -70.9375 a -70.3125), dentro de la zona de 1° × 1° que usa la app.
- El Niño: NOAA Climate Prediction Center, Oceanic Niño Index (ONI), Niño 3.4, ERSSTv5, estación DJF.
- Hoy: El Niño Advisory: El Niño fuerte a muy fuerte probable hasta enero-marzo 2027; Niño 3.4 +2,5 °C y Niño 1+2 +4,4 °C (ENSO Diagnostic Discussion, 12/11/2026). Alerta de El Niño Costero: magnitud extraordinaria hasta febrero 2027 (Comunicado Oficial ENFEN N.° 20-2026, 13/11/2026).
- Temporada = diciembre a marzo, 44 temporadas (1981-82 a 2024-25). Consultado el 2026-11-15.

## Resultados

- **Terciles de la normal 1991–2020:** bajo lo normal si la temporada tiene menos de 0,63 mm/día; sobre lo normal si tiene más de 0,87 mm/día.
- **Relación con El Niño:** Pearson r = -0,40, Spearman ρ = -0,31, valor p por permutación = 0,0064. Cada grado de ONI cambia la lluvia de la temporada en -0,113 mm/día.
- **¿Calibrar con El Niño acierta más?** En validación cruzada, el tercil se acierta en 16 de 44 temporadas (36,4 %, frente a 33,3 % del azar). Puntaje de Heidke: 0,011 (0 = azar, 1 = perfecto). Con todos los años mezclados, una recta casi no mejora el tercil: la señal no es pareja.
- **La señal está en los El Niño fuertes:** 4 de 5 fueron bajo lo normal. La regla "ONI ≥ 1,5 → bajo lo normal", validada dejando una temporada fuera, acierta 4 de 5 (80 % frente a 33 % del azar). La probabilidad de ver tantas temporadas secas por azar es 0,045. Esa es la calibración que importa hoy, con un El Niño muy fuerte.

| Fase (ONI DJF) | Temporadas | Lluvia media (mm/día) | Bajo lo normal | Normal | Sobre lo normal |
|---|---|---|---|---|---|
| El Niño fuerte | 5 | 0,446 | 4 | 1 | 0 |
| El Niño | 15 | 0,639 | 7 | 6 | 2 |
| Neutro | 13 | 0,835 | 3 | 4 | 6 |
| La Niña | 16 | 0,847 | 4 | 7 | 5 |

El Niño fuerte (ONI ≥ 1,5): 1982-83, 1991-92, 1997-98, 2015-16, 2023-24.

## Temporada 2026–27

Con ONI 2,46 (ASO 2026), la regresión espera **0,499 mm/día** (intervalo de 90 %: 0,000 a 1,005), es decir **bajo lo normal**. 4 de 5 temporadas con El Niño fuerte fueron bajo lo normal; 0 sobre lo normal.

Esto es evidencia histórica, no un pronóstico oficial. Para decisiones, usar los comunicados de ENFEN y los pronósticos de SENAMHI.

## Cómo suena (Sonic Visualiser: `salidas/sonic_visualiser/temporadas.wav`)

Una temporada por momento, con el mismo vocabulario de la app: **2 golpes = bajo lo normal, 4 = normal, 7 = sobre lo normal**. El rumor de fondo crece con la lluvia de la temporada. Las capas `temporadas_*.csv` marcan el año, la fase de El Niño y la curva del ONI.

| Temporada | Lluvia (mm/día) | ONI DJF | Fase | Tercil |
|---|---|---|---|---|
| 1981-82 | 0,785 | -0.05 | Neutro | normal |
| 1982-83 | 0,083 | +2.14 | El Niño fuerte | bajo lo normal |
| 1983-84 | 1,498 | -0.63 | La Niña | sobre lo normal |
| 1984-85 | 0,677 | -1.01 | La Niña | normal |
| 1985-86 | 0,870 | -0.40 | Neutro | sobre lo normal |
| 1986-87 | 0,750 | +1.18 | El Niño | normal |
| 1987-88 | 0,647 | +0.63 | El Niño | normal |
| 1988-89 | 0,863 | -1.64 | La Niña | normal |
| 1989-90 | 0,338 | +0.18 | Neutro | bajo lo normal |
| 1990-91 | 0,568 | +0.35 | Neutro | bajo lo normal |
| 1991-92 | 0,212 | +1.54 | El Niño fuerte | bajo lo normal |
| 1992-93 | 0,642 | +0.13 | Neutro | normal |
| 1993-94 | 0,858 | +0.07 | Neutro | normal |
| 1994-95 | 0,887 | +0.88 | El Niño | sobre lo normal |
| 1995-96 | 0,618 | -0.88 | La Niña | bajo lo normal |
| 1996-97 | 1,155 | -0.41 | Neutro | sobre lo normal |
| 1997-98 | 0,593 | +2.22 | El Niño fuerte | bajo lo normal |
| 1998-99 | 0,677 | -1.51 | La Niña | normal |
| 1999-00 | 1,357 | -1.47 | La Niña | sobre lo normal |
| 2000-01 | 1,160 | -0.76 | La Niña | sobre lo normal |
| 2001-02 | 1,288 | -0.15 | Neutro | sobre lo normal |
| 2002-03 | 0,823 | +0.90 | El Niño | normal |
| 2003-04 | 0,948 | +0.34 | Neutro | sobre lo normal |
| 2004-05 | 0,840 | +0.62 | El Niño | normal |
| 2005-06 | 1,282 | -0.86 | La Niña | sobre lo normal |
| 2006-07 | 0,520 | +0.62 | El Niño | bajo lo normal |
| 2007-08 | 0,835 | -1.76 | La Niña | normal |
| 2008-09 | 0,492 | -0.89 | La Niña | bajo lo normal |
| 2009-10 | 0,388 | +1.47 | El Niño | bajo lo normal |
| 2010-11 | 0,762 | -1.29 | La Niña | normal |
| 2011-12 | 1,120 | -0.71 | La Niña | sobre lo normal |
| 2012-13 | 0,840 | -0.24 | Neutro | normal |
| 2013-14 | 0,507 | -0.24 | Neutro | bajo lo normal |
| 2014-15 | 0,848 | +0.73 | El Niño | normal |
| 2015-16 | 0,603 | +2.50 | El Niño fuerte | bajo lo normal |
| 2016-17 | 0,917 | -0.08 | Neutro | sobre lo normal |
| 2017-18 | 0,672 | -0.71 | La Niña | normal |
| 2018-19 | 0,583 | +0.99 | El Niño | bajo lo normal |
| 2019-20 | 1,065 | +0.71 | El Niño | sobre lo normal |
| 2020-21 | 0,710 | -0.99 | La Niña | normal |
| 2021-22 | 0,453 | -0.76 | La Niña | bajo lo normal |
| 2022-23 | 0,378 | -0.55 | La Niña | bajo lo normal |
| 2023-24 | 0,738 | +1.84 | El Niño fuerte | normal |
| 2024-25 | 1,140 | -0.46 | Neutro | sobre lo normal |

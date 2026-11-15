# Pacha Takiy · Fundamento matemático

Este documento justifica cada decisión: de dónde sale cada número, qué fórmula lo transforma en sonido o vibración, por qué esa fórmula es perceptible para una persona y cómo se verificó. Todas las cifras se pueden reproducir con `sonic_visualiser.bat` y `probar.bat`: 228 pruebas automáticas, de las que 227 pasan y 1 es una falla esperada que documenta un hallazgo.

---

## 0. Qué pide el reto y cómo se cumple

El reto *The Earth Information Jukebox* pide hacer accesible la ciencia de la Tierra uniendo **visualizaciones del Earth Information Center (EIC)** con **sonificaciones generadas en tiempo real**.

| Lo que pide el reto | Cómo lo cumple Pacha Takiy | Dato de NASA |
|---|---|---|
| Visual del EIC | Vista mundial de lluvia **SVS 4285** (Earth Information Center) y recorte de Moquegua | NASA SVS 4285, GPM IMERG |
| Sonificación en tiempo real | Motor Web Audio: los golpes y el rumor se calculan en el navegador a partir del dato | GPM IMERG vía NASA GIBS |
| Accesible y multisensorial | Modos Escuchar, Ver y Todo junto, vibración y lector de pantalla | — |
| Rigor científico | Regla fija y pública, verificación con modelo matemático y estadística | NASA POWER (MERRA-2) |
| Relevancia actual | Calibración con **El Niño** (NOAA, socio de NASA en el monitoreo de ENSO) | NASA POWER + NOAA ONI |

---

## 1. Datos

| Dato | Fuente | Resolución | Incertidumbre conocida |
|---|---|---|---|
| Lluvia cada 30 min, 10/02/2025 | NASA GPM IMERG (`IMERG_Precipitation_Rate_30min`, GIBS) | 0,1° (~10 km) | Estimación satelital; puede diferir de pluviómetros de SENAMHI |
| Lluvia mensual 1981–2025 | NASA POWER v2.10 (`PRECTOTCORR`, MERRA-2) | 0,5° × 0,625° | Reanálisis; un mes atípico (set. 2022) se reporta aparte |
| El Niño | NOAA CPC, Oceanic Niño Index (ONI, Niño 3.4) | 3 meses | Índice oficial de ENSO |
| Mapa | INEI, límites provinciales | ~0,004° simplificado | Solo para ubicar |

---

## 2. Del píxel al dato (regla del equipo, `scripts/clasificacion.py`)

Cada píxel $p$ con alfa $\ge 32$ cuenta como lluvia. Su color $\mathbf{x}_p=(r,g,b)$ se asigna al color $\mathbf{c}_j$ de la leyenda oficial de NASA GIBS con la menor distancia euclídea:

$$j^*(p)=\arg\min_j \lVert \mathbf{x}_p-\mathbf{c}_j\rVert_2,\qquad \text{válido si } \lVert \mathbf{x}_p-\mathbf{c}_{j^*}\rVert_2<28$$

- **Cobertura** (área con lluvia): $c=\dfrac{N_\text{lluvia}}{N_\text{total}}$, con $N_\text{total}=10\,000$ píxeles, es decir 100 celdas de 0,1°.
- **Intensidad del momento:** la **mediana** de las clases AMS de los píxeles reconocidos. La mediana es robusta a píxeles extremos. Los cortes son 2,5 y 7,6 mm/h, ajustados a los límites de color de la leyenda: 2,5119 y 7,4989.
- **Momento ilegible:** si $N_\text{ambiguos}/N_\text{lluvia}>0{,}20$. Así se evita sonificar un dato dudoso.

---

## 3. Del dato al sonido (`web/js/audio.js`, modelado en `scripts/modelo_acustico.py`)

### 3.1 Golpes = intensidad
Con $n\in\{2,4,7\}$ golpes para las clases baja, media y alta, en una ventana $T=1{,}5$ s:

$$t_i=t_0+i\,\frac{T}{n},\qquad i=0,\dots,n-1$$

Cada golpe es un seno de $f=440$ Hz con envolvente exponencial, la misma rampa de la Web Audio API:

$$g(t)=\begin{cases}g_0\left(\dfrac{g_1}{g_0}\right)^{t/t_a} & 0\le t\le t_a\\[2mm] g_1\left(\dfrac{g_0}{g_1}\right)^{(t-t_a)/(t_d-t_a)} & t_a<t\le t_d\end{cases}$$

con $g_0=10^{-4}$, $g_1=0{,}5$, $t_a=5$ ms y $t_d=85$ ms.

**Por qué se pueden contar:** el silencio mínimo entre golpes es $T/7-t_d=129$ ms, mayor que los 100 ms que el oído necesita para separar dos eventos.

### 3.2 Rumor = área con lluvia
Ruido uniforme $u\sim U(-1,1)$ (varianza $\sigma^2=1/3$) que pasa por un filtro pasabanda biquad (estándar W3C, $f_c=1200$ Hz, $Q=0{,}7$) con ganancia:

$$\text{nivel}(c)=0{,}03+0{,}22\cdot\min\!\left(1,\frac{c}{0{,}4}\right)$$

Su valor RMS se predice en forma cerrada:

$$\text{RMS}=\text{nivel}(c)\cdot v\cdot\frac{1}{\sqrt3}\cdot\sqrt{G},\qquad G=\frac1\pi\int_0^\pi\lvert H(e^{j\omega})\rvert^2d\omega=0{,}1005$$

donde $v$ es el volumen.

### 3.3 Por qué es perceptible (psicoacústica)
- **Umbral diferencial (Weber–Fechner):** el oído distingue cambios de nivel de ruido de ≈1 dB. Diferencia entre A y B:
  $$\Delta L=20\log_{10}\frac{\text{nivel}(c_A)}{\text{nivel}(c_B)}=4{,}9\ \text{dB}$$
  Es cinco veces el umbral.
- **Sonoridad (ley de Stevens):** la sonoridad se duplica cada 10 dB, así que A se percibe $2^{\Delta L/10}=1{,}41$ veces más fuerte que B.
- **Enmascaramiento (banda crítica de Glasberg y Moore):**
  $$\text{ERB}(f)=24{,}7\,(4{,}37f/1000+1)\approx72\ \text{Hz a 440 Hz}$$
  $$\text{margen}=10\log_{10}\frac{g_1^2/2}{\sigma^2\,\frac{2\,\text{ERB}}{f_s}\,\lvert H(440)\rvert^2\,\text{nivel}^2}\ \ge\ 38\ \text{dB}$$
  El rumor nunca tapa un golpe.
- **Seguridad visual (WCAG 2.3.1):** 7 golpes en 1,5 s serían 4,7 destellos por segundo, por encima del máximo de 3. Por eso el visor muestra puntos que se llenan, no destellos.

### 3.4 Capacidad de información
- **Golpes:** 3 categorías, es decir $\log_2 3=1{,}58$ bits por momento.
- **Rumor:** rango $20\log_{10}(0{,}25/0{,}03)=18{,}4$ dB. Dividido por un umbral de 1 dB da ≈18 niveles distinguibles, $\log_2 18\approx4{,}2$ bits.
- **Hallazgo:** con la curva lineal, 3 puntos de cobertura suben menos de 1 dB cuando $c>19\,\%$. **Propuesta** con los mismos extremos pero lineal en decibeles:
  $$\text{nivel}'(c)=0{,}03\left(\frac{0{,}25}{0{,}03}\right)^{\min(1,c/0{,}4)}\ \Rightarrow\ \frac{d\,L}{d\,c}=\frac{18{,}4}{40}=0{,}46\ \text{dB por punto}$$
  Así 3 puntos dan 1,38 dB con cualquier cobertura.

---

## 4. Verificación: lo que suena es el dato

- **Detector de golpes (algoritmo de Goertzel):** cuadros de $N=240$ muestras (5 ms) con ventana de Hann.
  $$s_k=x_k+2\cos(2\pi f/f_s)\,s_{k-1}-s_{k-2},\qquad \lvert X(f)\rvert^2=s_{N}^2+s_{N-1}^2-2\cos(2\pi f/f_s)\,s_Ns_{N-1}$$
  Un golpe empieza donde la envolvente cruza la mitad de su rango dinámico.
- **Criterio de aceptación:** número de golpes exacto, error de tiempo $\le 12$ ms y rumor medido a $\pm1$ dB del previsto.
- **Resultados:**
  - modelo: 1,9 ms de error máximo;
  - **audio real de la web**, capturado con `OfflineAudioContext`: rumor a ±0,17 dB y 9 de 9 momentos con los golpes exactos;
  - retardo fijo del limitador: 8,1 ms.
- **Robustez de la respuesta A/B (bootstrap pareado de las 100 celdas, 10 000 réplicas):**
  $$c_A-c_B=13{,}3\ \text{puntos},\qquad \text{IC}_{95\%}=[5{,}0;\ 21{,}9]$$
  El intervalo no incluye 0 y su mínimo supera el umbral de 3 puntos de la app.

---

## 5. Dónde llueve (`scripts/geografia.py`)

Cada celda $(i,j)$ de 0,1° tiene fracción de lluvia $f_{ij}$. El centro de la lluvia es el centroide ponderado:

$$\bar\imath=\frac{\sum f_{ij}\,i}{\sum f_{ij}},\qquad \bar\jmath=\frac{\sum f_{ij}\,j}{\sum f_{ij}}$$

y se traduce a palabras (norte, sur, este, oeste). En los 6 momentos del episodio, la lluvia está al **noreste, en la cuenca alta hacia Carumas**.

---

## 6. El Niño y la lluvia de la cuenca alta (`scripts/enso_moquegua.py`)

**Temporada de lluvias** $Y$ = diciembre de $Y-1$ a marzo de $Y$:
$$P_Y=\tfrac14\,(P_\text{dic}+P_\text{ene}+P_\text{feb}+P_\text{mar})\quad\text{(mm/día)}$$
Se usan 44 temporadas (1981-82 a 2024-25).

- **Terciles de la normal OMM 1991–2020:** $q_{1/3}=0{,}634$ y $q_{2/3}=0{,}867$ mm/día. Debajo de $q_{1/3}$ es "bajo lo normal"; encima de $q_{2/3}$, "sobre lo normal".
- **Correlación con el ONI** (Pearson): $r=-0{,}40$. Spearman: $\rho=-0{,}31$.
- **Significancia sin suponer normalidad** (prueba de permutación con 20 000 permutaciones):
  $$p=\frac{1+\#\{\lvert r_\pi\rvert\ge\lvert r\rvert\}}{1+20\,000}=0{,}006$$
- **Regresión:** $\hat P=0{,}777-0{,}113\cdot\text{ONI}$, con $s=0{,}282$ mm/día.
  - Intervalo de predicción al 90 %:
    $$\hat P\pm t_{0{,}95;42}\,s\sqrt{1+\frac1n+\frac{(\text{ONI}-\overline{\text{ONI}})^2}{\sum(\text{ONI}_i-\overline{\text{ONI}})^2}}$$
- **Validación cruzada dejando una temporada fuera** (todas las temporadas):
  - aciertos del tercil: 36,4 % frente a 33,3 % del azar;
  - puntaje de Heidke: $\text{HSS}=\dfrac{H-E}{N-E}=0{,}011$.
  - Una recta sobre todos los años casi no ayuda: la señal no es pareja.
- **La señal está en El Niño fuerte** (ONI ≥ 1,5):
  - 4 de 5 temporadas fueron bajo lo normal;
  - la regla "ONI ≥ 1,5 → bajo lo normal" acierta 4 de 5 dejando una fuera (80 %);
  - probabilidad de ese resultado por azar:
    $$P(X\ge4)=\sum_{k=4}^{5}\binom5k\left(\tfrac13\right)^k\left(\tfrac23\right)^{5-k}=0{,}045$$
- **Temporada 2026–27:** con ONI = 2,46 (ASO 2026), $\hat P=0{,}50$ mm/día, intervalo de 90 % de 0 a 1,0 mm/día: **bajo lo normal**. Es evidencia histórica, no un pronóstico oficial (SENAMHI y ENFEN).

**Sonificación de las temporadas** (el mismo vocabulario de la app):
- golpes: $n=\{2,4,7\}$ según el tercil;
- rumor: $c=0{,}4\cdot P_Y/\max P$.

---

## 7. Háptica (vibración)

- **Cada golpe:** 45 ms de vibración, sincronizada con el audio a menos de 8 ms.
- **"Sentir el área":** pulsos de 25 ms con pausa $\tau=220-190\,\phi$ ms, donde $\phi\in[0,1]$ es el nivel relativo del rumor. La densidad de pulsos es
  $$\rho=\frac{1}{25+\tau}$$
  y crece de forma monótona con el área: de 4 pulsos/s cuando $\phi=0$ a 18 pulsos/s cuando $\phi=1$.

---

## 8. Límites (honestidad científica)
- IMERG y MERRA-2 son estimaciones satelitales o de modelo, no mediciones de pluviómetro.
- La celda de NASA POWER (~50 km) mezcla valle y cuenca alta.
- 5 temporadas con El Niño fuerte son una muestra pequeña; por eso se reporta la probabilidad de azar (0,045) y no se vende como pronóstico.
- Setiembre de 2022 tiene un valor atípico de MERRA-2 (10,5 mm/día en época seca); no afecta a las temporadas de diciembre a marzo.

---

## 9. Reproducir
```bat
sonic_visualiser.bat     :: El Niño, audios, capas, sesiones .sv, reportes y visor
probar.bat               :: 228 pruebas (Python) + web y captura del audio real (Node)
```
Reportes: `pruebas/reportes/acustica.md` y `pruebas/reportes/enso.md`. Sesiones para Sonic Visualiser: `salidas/sonic_visualiser/*.sv`.

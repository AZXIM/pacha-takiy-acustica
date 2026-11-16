"""
Pacha Takiy: analizador acústico de un WAV (lo mismo que se mira en Sonic Visualiser, pero automático).

Mide en el audio, sin conocer cómo se generó:
  * los golpes de 440 Hz (detector de inicios con el algoritmo de Goertzel, cuadros de 5 ms),
  * el nivel del rumor de fondo entre golpes (RMS en dBFS),
  * el pico de la señal (para saber si el limitador actúa o si recorta).

Luego compara contra la partitura del modelo (modelo_acustico.py) y dice, momento por momento,
si suena lo que promete la regla. Funciona igual con el WAV del modelo, con una captura de la web
(pruebas/web/acustica.spec.js) o con una grabación del celular.
"""
import math
import statistics

import modelo_acustico as ma

CUADRO_S = 0.005            # cuadro de análisis: 5 ms
SALTO_S = 0.0025            # salto entre cuadros: 2,5 ms
REFRACTARIO_S = 0.06        # dos inicios a menos de 60 ms cuentan como uno
TOLERANCIA_TIEMPO_S = 0.012 # error de tiempo aceptado por golpe (también absorbe el retardo del limitador)


def goertzel_envolvente(x, fs, f=440.0, cuadro_s=CUADRO_S, salto_s=SALTO_S):
    """Amplitud de la componente de f Hz en cada cuadro (ventana de Hann). Devuelve (tiempos, amplitudes)."""
    n, h = int(cuadro_s * fs), int(salto_s * fs)
    ven = [0.5 - 0.5 * math.cos(2 * math.pi * i / (n - 1)) for i in range(n)]
    norma = sum(ven) / 2
    coef = 2 * math.cos(2 * math.pi * f / fs)
    tiempos, amp = [], []
    for i0 in range(0, len(x) - n, h):
        s1 = s2 = 0.0
        for i in range(n):
            s0 = x[i0 + i] * ven[i] + coef * s1 - s2
            s2, s1 = s1, s0
        potencia = s1 * s1 + s2 * s2 - coef * s1 * s2
        tiempos.append((i0 + n / 2) / fs)
        amp.append(math.sqrt(max(potencia, 0.0)) / norma)
    return tiempos, amp


def detectar_golpes(x, fs, f=440.0):
    """Instantes (s) donde empieza un golpe de f Hz: cruce hacia arriba de la mitad del rango dinámico."""
    t, a = goertzel_envolvente(x, fs, f)
    if not a:
        return []
    piso, techo = statistics.median(a), max(a)
    if techo < 1e-3 or techo < 4 * max(piso, 1e-6):
        return []
    umbral = piso + 0.5 * (techo - piso)
    inicios, ultimo = [], -1.0
    for i in range(1, len(a)):
        if a[i - 1] < umbral <= a[i] and t[i] - ultimo > REFRACTARIO_S:
            # Interpolación lineal del cruce y corrección por la mitad del cuadro (el centro va adelantado)
            frac = (umbral - a[i - 1]) / (a[i] - a[i - 1])
            cruce = t[i - 1] + frac * (t[i] - t[i - 1]) - CUADRO_S / 2
            inicios.append(cruce)
            ultimo = t[i]
    return inicios


def rms_db(x):
    return ma.db(math.sqrt(sum(v * v for v in x) / max(1, len(x))))


def medir_momento(x, fs, momento, k, golpes_detectados):
    """Nivel del rumor en la parte estable del momento, lejos de los golpes (±40 ms después de cada uno)."""
    a, b = momento["inicio"] + k["RUMOR_SUBIDA"] + 0.02, momento["fin"] - k["RUMOR_BAJADA"] - 0.02
    zonas = [(g, g + k["DURACION_GOLPE"] + 0.04) for g in golpes_detectados]
    trozo = [x[i] for i in range(int(a * fs), min(len(x), int(b * fs)))
             if not any(z0 <= i / fs <= z1 for z0, z1 in zonas)]
    return rms_db(trozo) if trozo else None


def comparar(x, fs, momentos, k, volumen=ma.VOLUMEN_DEFECTO, desfase_s=0.0, ganancia_db=0.0):
    """Compara la señal con la partitura. desfase_s y ganancia_db corrigen el retardo y la ganancia fija
    del limitador cuando se analiza una captura de la web. Devuelve una fila por momento."""
    detectados = detectar_golpes(x, fs, k["FRECUENCIA"])
    filas = []
    for m in momentos:
        ventana = [g - desfase_s for g in detectados if m["inicio"] - 0.03 <= g - desfase_s <= m["fin"]]
        errores = [min(abs(g - e) for e in m["golpes"]) for g in ventana] if m["golpes"] else []
        medido = medir_momento(x, fs, {**m, "inicio": m["inicio"] + desfase_s, "fin": m["fin"] + desfase_s}, k,
                               [g + desfase_s for g in ventana])
        previsto = ma.db(ma.rms_rumor_previsto(m["rumor"], k, volumen)) if m["rumor"] > 0 else None
        if medido is not None:
            medido -= ganancia_db
        ioi = [b - a for a, b in zip(m["golpes"], m["golpes"][1:])]
        filas.append({
            "hora": m["hora"], "clase": m["clase"], "cobertura": m["cobertura"],
            "golpes_esperados": m["pulsos"], "golpes_medidos": len(ventana),
            "error_max_ms": round(1000 * max(errores), 1) if errores else 0.0,
            "separacion_min_s": round(min(ioi) - k["DURACION_GOLPE"], 3) if ioi else None,
            "rumor_previsto_db": round(previsto, 2) if previsto is not None else None,
            "rumor_medido_db": round(medido, 2) if (medido is not None and previsto is not None) else None,
            "margen_enmascaramiento_db": round(ma.margen_enmascaramiento_db(m["rumor"], k), 1) if m["rumor"] else None,
        })
    for fila in filas:
        fila["ok"] = (fila["golpes_medidos"] == fila["golpes_esperados"]
                      and fila["error_max_ms"] <= 1000 * TOLERANCIA_TIEMPO_S
                      and (fila["rumor_previsto_db"] is None or fila["rumor_medido_db"] is None
                           or abs(fila["rumor_medido_db"] - fila["rumor_previsto_db"]) <= 1.0))
    return filas


def energia_golpe_db(x, fs, inicio, largo_s=0.11):
    """Energía (dB) de la señal en los largo_s segundos que siguen a un golpe."""
    i0 = int(inicio * fs)
    return 10 * math.log10(sum(v * v for v in x[i0:i0 + int(largo_s * fs)]) + 1e-12)


def pico_dbfs(x):
    return ma.db(max((abs(v) for v in x), default=0.0))


def estimar_alineacion(x, fs, momentos, k):
    """Retardo (s) entre la partitura y la captura: mediana de (golpe medido − golpe previsto más cercano)."""
    previstos = [g for m in momentos for g in m["golpes"]]
    medidos = detectar_golpes(x, fs, k["FRECUENCIA"])
    if not previstos or not medidos:
        return 0.0
    difs = [g - min(previstos, key=lambda e: abs(e - g)) for g in medidos]
    return statistics.median(difs)

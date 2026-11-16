"""
Pacha Takiy: modelo matemático del sonido (gemelo de web/js/audio.js).

Para qué sirve
--------------
La regla del proyecto dice qué debe sonar (golpes por intensidad, rumor por cobertura).
Este módulo lo convierte en un modelo con fórmulas para poder comprobar, con números
y sin oído humano, que el sonido que genera la web es el que promete la regla:

1. Lee las constantes de la fuente de verdad (web/js/reglas.js y web/js/audio.js).
   Si alguien cambia audio.js, las pruebas avisan de inmediato.
2. Arma la "partitura": el instante exacto de cada golpe y el nivel del rumor.
3. Sintetiza la señal muestra por muestra con las mismas ecuaciones de la Web Audio API
   (rampas exponenciales y lineales, filtro biquad pasabanda del estándar W3C).
4. Predice con fórmulas cerradas lo que debe medirse: nivel RMS del rumor, margen de
   enmascaramiento de los golpes y la diferencia mínima de cobertura que se puede oír.

Solo usa la biblioteca estándar de Python, como el resto de scripts/.
NO cambia la regla del equipo: solo la describe y la verifica.
"""
import math
import random
import re
import struct
import wave
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUTA_REGLAS_JS = RAIZ / "web" / "js" / "reglas.js"
RUTA_AUDIO_JS = RAIZ / "web" / "js" / "audio.js"
RUTA_EPISODIO = RAIZ / "datos" / "episodio_moquegua.json"

FS = 48_000                 # frecuencia de muestreo de referencia (la de casi todos los navegadores)
VOLUMEN_DEFECTO = 0.8       # pref.volumen por defecto (web/js/estado.js)

# Psicoacústica (valores de referencia conservadores)
JND_RUIDO_DB = 1.0          # menor diferencia de nivel de un ruido que una persona nota (0,5 a 1 dB; Miller, 1947)
MARGEN_COMODO_DB = 2.0      # diferencia que se oye sin esfuerzo, con parlantes de celular o laptop
MARGEN_ENMASCARAMIENTO_DB = 10.0   # el golpe debe superar al rumor en su banda crítica por al menos esto
SEPARACION_MIN_S = 0.10     # silencio mínimo entre golpes para poder contarlos uno por uno


class CambioEnAudioJS(RuntimeError):
    """audio.js o reglas.js cambiaron y el modelo ya no los describe."""


# ----------------------------------------------------------------------------------------------
# 1. Constantes leídas de la web (una sola fuente de verdad)
# ----------------------------------------------------------------------------------------------
def _numero(texto, patron, nombre, archivo):
    m = re.search(patron, texto)
    if not m:
        raise CambioEnAudioJS(f"No encontré {nombre} en {archivo.name}. Si cambió el motor de audio, actualiza modelo_acustico.py.")
    return float(m.group(1))


def leer_constantes(reglas=RUTA_REGLAS_JS, audio=RUTA_AUDIO_JS):
    """Devuelve un dict con todas las constantes que definen el sonido, tal como están en la web."""
    r = Path(reglas).read_text(encoding="utf-8")
    a = Path(audio).read_text(encoding="utf-8")
    c = {}
    for nombre in ("VENTANA_S", "SILENCIO_S", "FRECUENCIA", "DURACION_GOLPE", "VIBRA_MS", "COBERTURA_MAX"):
        c[nombre] = _numero(r, rf"export const {nombre}\s*=\s*([\d.]+)", nombre, Path(reglas))
    m = re.search(r"export const PULSOS\s*=\s*\{([^}]*)\}", r)
    if not m:
        raise CambioEnAudioJS("No encontré PULSOS en reglas.js.")
    c["PULSOS"] = {int(k): int(v) for k, v in re.findall(r"(\d+)\s*:\s*(\d+)", m.group(1))}

    golpe = a[a.index("golpe(t)"):a.index("rumor(t, cobertura)")]
    c["GOLPE_PICO"] = _numero(golpe, r"exponentialRampToValueAtTime\(([\d.]+),\s*t \+ [\d.]+\)", "el pico del golpe", Path(audio))
    c["GOLPE_ATAQUE"] = _numero(golpe, r"exponentialRampToValueAtTime\([\d.]+,\s*t \+ ([\d.]+)\)", "el ataque del golpe", Path(audio))
    c["GOLPE_PISO"] = _numero(golpe, r"setValueAtTime\(([\d.]+),\s*t\)", "el piso del golpe", Path(audio))
    c["GOLPE_COLA"] = _numero(golpe, r"o\.stop\(t \+ DURACION_GOLPE \+ ([\d.]+)\)", "la cola del golpe", Path(audio))

    rumor = a[a.index("rumor(t, cobertura)"):a.index("reproducir(pulsos")]
    c["RUMOR_BASE"] = _numero(rumor, r"nivel = ([\d.]+) \+", "el nivel base del rumor", Path(audio))
    c["RUMOR_RANGO"] = _numero(rumor, r"nivel = [\d.]+ \+ ([\d.]+) \*", "el rango del rumor", Path(audio))
    c["RUMOR_FC"] = _numero(rumor, r"f\.frequency\.value = ([\d.]+)", "la frecuencia del filtro", Path(audio))
    c["RUMOR_Q"] = _numero(rumor, r"f\.Q\.value = ([\d.]+)", "el Q del filtro", Path(audio))
    c["RUMOR_SUBIDA"] = _numero(rumor, r"linearRampToValueAtTime\(nivel, t \+ ([\d.]+)\)", "la subida del rumor", Path(audio))
    c["RUMOR_BAJADA"] = _numero(rumor, r"setValueAtTime\(nivel, t \+ VENTANA_S - ([\d.]+)\)", "la bajada del rumor", Path(audio))
    if "Math.min(1, cobertura / COBERTURA_MAX)" not in rumor:
        raise CambioEnAudioJS("Cambió la fórmula del rumor en audio.js. Actualiza nivel_rumor() en modelo_acustico.py.")

    rep = a[a.index("reproducir(pulsos"):]
    c["INICIO"] = _numero(rep, r"const t0 = ctx\.currentTime \+ ([\d.]+)", "el retardo de inicio", Path(audio))
    c["LIM_UMBRAL_DB"] = _numero(a, r"lim\.threshold\.value = (-?[\d.]+)", "el umbral del limitador", Path(audio))
    return c


# ----------------------------------------------------------------------------------------------
# 2. La regla en fórmulas
# ----------------------------------------------------------------------------------------------
def nivel_rumor(cobertura, k):
    """Ganancia del rumor según audio.js: base + rango · min(1, c / COBERTURA_MAX). 0 si no hay cobertura."""
    if not cobertura or cobertura <= 0:
        return 0.0
    return k["RUMOR_BASE"] + k["RUMOR_RANGO"] * min(1.0, cobertura / k["COBERTURA_MAX"])


def nivel_rumor_propuesto(cobertura, k):
    """PROPUESTA (requiere acuerdo del equipo): misma ganancia mínima y máxima, pero la curva va en decibeles.
    Cada punto de cobertura sube el rumor la misma cantidad de dB, así 3 puntos siempre se oyen igual de claro."""
    if not cobertura or cobertura <= 0:
        return 0.0
    g0, g1 = k["RUMOR_BASE"], k["RUMOR_BASE"] + k["RUMOR_RANGO"]
    return g0 * (g1 / g0) ** min(1.0, cobertura / k["COBERTURA_MAX"])


def db(x):
    return 20 * math.log10(max(x, 1e-12))


def partitura(fotogramas, k, secuencia=True):
    """Lista de momentos con el instante exacto de cada golpe (s), la ganancia del rumor y la ventana.
    secuencia=True replica el paso 5 (1,5 s de sonido + 1 s de silencio); False, un solo momento."""
    momentos, t = [], k["INICIO"]
    for f in fotogramas:
        pulsos = f.get("pulsos", 0) if f.get("estado") == "ok" else 0
        paso = k["VENTANA_S"] / pulsos if pulsos else 0
        momentos.append({
            "id": f.get("id"), "hora": f.get("hora_peru", ""), "clase": f.get("clase_nombre"),
            "estado": f.get("estado"), "cobertura": f.get("cobertura") or 0.0, "pulsos": pulsos,
            "inicio": t, "fin": t + k["VENTANA_S"],
            "golpes": [t + i * paso for i in range(pulsos)],
            "rumor": nivel_rumor(f.get("cobertura") or 0.0, k),
        })
        t += k["VENTANA_S"] + (k["SILENCIO_S"] + 0.12 if secuencia else 0.5)
    return momentos


# ----------------------------------------------------------------------------------------------
# 3. Síntesis fiel a la Web Audio API (W3C Web Audio API 1.0)
# ----------------------------------------------------------------------------------------------
def coeficientes_pasabanda(fc, q, fs=FS):
    """BiquadFilterNode tipo "bandpass" según el estándar W3C (fórmulas de R. Bristow-Johnson)."""
    w0 = 2 * math.pi * fc / fs
    alfa = math.sin(w0) / (2 * q)
    a0 = 1 + alfa
    return (alfa / a0, 0.0, -alfa / a0), (1.0, -2 * math.cos(w0) / a0, (1 - alfa) / a0)


def respuesta(b, a, f, fs=FS):
    """|H(f)| del biquad."""
    w = 2 * math.pi * f / fs
    z1, z2 = complex(math.cos(-w), math.sin(-w)), complex(math.cos(-2 * w), math.sin(-2 * w))
    return abs((b[0] + b[1] * z1 + b[2] * z2) / (a[0] + a[1] * z1 + a[2] * z2))


def ganancia_potencia_ruido(b, a, fs=FS, n=20000):
    """Fracción de la potencia de un ruido blanco que deja pasar el filtro: (1/π)∫|H(e^jw)|² dw."""
    return sum(respuesta(b, a, (i + 0.5) * (fs / 2) / n, fs) ** 2 for i in range(n)) / n


def _exp(v0, v1, t0, t1, t):
    return v0 * (v1 / v0) ** ((t - t0) / (t1 - t0))


def envolvente_golpe(t, k):
    """Ganancia del golpe t segundos después de empezar (setValue → exponentialRamp → exponentialRamp)."""
    piso, pico, at, dur = k["GOLPE_PISO"], k["GOLPE_PICO"], k["GOLPE_ATAQUE"], k["DURACION_GOLPE"]
    if t < 0 or t >= dur + k["GOLPE_COLA"]:
        return 0.0
    if t <= at:
        return _exp(piso, pico, 0, at, t)
    if t <= dur:
        return _exp(pico, piso, at, dur, t)
    return piso


def envolvente_rumor(t, nivel, k):
    """Ganancia del rumor t segundos después de empezar (lineal sube, se mantiene, lineal baja)."""
    v, sube, baja = k["VENTANA_S"], k["RUMOR_SUBIDA"], k["RUMOR_BAJADA"]
    piso = 0.0001
    if t < 0 or t >= v + 0.05:
        return 0.0
    if t <= sube:
        return piso + (nivel - piso) * t / sube
    if t <= v - baja:
        return nivel
    if t <= v:
        return nivel + (piso - nivel) * (t - (v - baja)) / baja
    return piso


def sintetizar(momentos, k, volumen=VOLUMEN_DEFECTO, fs=FS, semilla=7, cola_s=0.4):
    """Señal mono (lista de floats) ANTES del limitador, igual que la suma que llega a Motor.maestro."""
    fin = max(m["fin"] for m in momentos) + cola_s
    n = int(fin * fs)
    y = [0.0] * n
    w = 2 * math.pi * k["FRECUENCIA"] / fs
    largo_golpe = int((k["DURACION_GOLPE"] + k["GOLPE_COLA"]) * fs)
    for m in momentos:
        for tg in m["golpes"]:
            i0 = round(tg * fs)
            for j in range(largo_golpe):
                if 0 <= i0 + j < n:
                    y[i0 + j] += envolvente_golpe(j / fs, k) * math.sin(w * j)
    # Rumor: ruido uniforme [-1, 1] de 2 s en bucle (como Motor.ruido) → pasabanda → envolvente
    rng = random.Random(semilla)
    ruido = [rng.uniform(-1, 1) for _ in range(2 * fs)]
    b, a = coeficientes_pasabanda(k["RUMOR_FC"], k["RUMOR_Q"], fs)
    for m in momentos:
        if m["rumor"] <= 0:
            continue
        i0, largo = round(m["inicio"] * fs), int((k["VENTANA_S"] + 0.05) * fs)
        x1 = x2 = y1 = y2 = 0.0
        for j in range(largo):
            x0 = ruido[j % len(ruido)]
            s = b[0] * x0 + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
            x2, x1, y2, y1 = x1, x0, y1, s
            if i0 + j < n:
                y[i0 + j] += envolvente_rumor(j / fs, m["rumor"], k) * s
    return [v * volumen for v in y]


# ----------------------------------------------------------------------------------------------
# 4. Predicciones analíticas (lo que el analizador debe medir)
# ----------------------------------------------------------------------------------------------
def rms_rumor_previsto(nivel, k, volumen=VOLUMEN_DEFECTO, fs=FS):
    """RMS del rumor estable: nivel · volumen · σ_ruido · sqrt(ganancia de potencia del filtro). σ = 1/√3."""
    b, a = coeficientes_pasabanda(k["RUMOR_FC"], k["RUMOR_Q"], fs)
    return nivel * volumen * (1 / math.sqrt(3)) * math.sqrt(ganancia_potencia_ruido(b, a, fs))


def erb(f):
    """Ancho de banda rectangular equivalente del oído en f (Glasberg y Moore, 1990), en Hz."""
    return 24.7 * (4.37 * f / 1000 + 1)


def margen_enmascaramiento_db(nivel, k, fs=FS):
    """Cuántos dB supera el golpe (seno de 440 Hz) al ruido del rumor dentro de la banda crítica del oído en 440 Hz.
    Potencia del golpe: A²/2. Ruido en la banda: (σ² · 2·ERB/fs) · |H(440)|² · nivel²."""
    if nivel <= 0:
        return float("inf")
    b, a = coeficientes_pasabanda(k["RUMOR_FC"], k["RUMOR_Q"], fs)
    f = k["FRECUENCIA"]
    p_golpe = k["GOLPE_PICO"] ** 2 / 2
    p_ruido = (1 / 3) * (2 * erb(f) / fs) * respuesta(b, a, f, fs) ** 2 * nivel ** 2
    return 10 * math.log10(p_golpe / p_ruido)


def diferencia_minima_audible(c, k, curva=nivel_rumor, jnd_db=JND_RUIDO_DB):
    """Menor aumento de cobertura (fracción) desde c que sube el rumor al menos jnd_db. None si satura antes."""
    base = curva(c, k)
    objetivo = base * 10 ** (jnd_db / 20)
    paso, dc = 0.0005, 0.0
    while c + dc <= k["COBERTURA_MAX"] + 1e-9:
        dc += paso
        if curva(c + dc, k) >= objetivo:
            return dc
    return None


def sonios(delta_db):
    """Cuántas veces más fuerte se percibe (ley de Stevens: la sonoridad se duplica cada 10 dB)."""
    return 2 ** (delta_db / 10)


# ----------------------------------------------------------------------------------------------
# 5. Archivos de audio
# ----------------------------------------------------------------------------------------------
def escribir_wav(ruta, muestras, fs=FS):
    """WAV mono de 16 bits. Recorta a [-1, 1] (si recorta, lo dice el reporte por el pico)."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(fs)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1.0, min(1.0, v)) * 32767)) for v in muestras))


def leer_wav(ruta):
    """(muestras mono en [-1, 1], fs). Acepta 16 bits, mono o estéreo (promedia canales)."""
    with wave.open(str(ruta), "rb") as w:
        fs, ch, ancho, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        if ancho != 2:
            raise ValueError("Solo WAV de 16 bits.")
        datos = struct.unpack(f"<{n * ch}h", w.readframes(n))
    return [sum(datos[i * ch:(i + 1) * ch]) / ch / 32768 for i in range(n)], fs

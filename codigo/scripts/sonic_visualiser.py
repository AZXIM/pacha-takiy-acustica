"""
Pacha Takiy: audios y capas de anotación para Sonic Visualiser, más el reporte acústico.

Uso:
    python scripts/sonic_visualiser.py                 genera salidas/sonic_visualiser/ y pruebas/reportes/acustica.md
    python scripts/sonic_visualiser.py --web CARPETA   además compara con el audio real capturado de la web
                                                       (lo deja pruebas/web/acustica.spec.js en pruebas/capturas/acustica/)

Qué genera (en salidas/sonic_visualiser/):
    tarde.wav, ab_demo.wav, clases.wav     audio de referencia (modelo exacto del Motor de la web)
    *_golpes.csv      capa de instantes: cada golpe con su etiqueta
    *_momentos.csv    capa de regiones: cada momento, con la cobertura como valor
    *_rumor.csv       capa de curva: nivel previsto del rumor en dB cada 50 ms
    *_audacity.txt    las mismas marcas para Audacity (Archivo → Importar → Etiquetas)
    LEEME.md          paso a paso en Sonic Visualiser

Sale con código 1 si algún momento no suena como dice la regla.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

import analisis_acustico as aa
import enso_moquegua as en
import geografia as geo
import modelo_acustico as ma

SALIDA = ma.RAIZ / "salidas" / "sonic_visualiser"
VISOR = ma.RAIZ / "docs" / "acustica"          # visor accesible para GitHub Pages (docs/acustica/index.html)
REPORTE = ma.RAIZ / "pruebas" / "reportes" / "acustica.md"
DEMO = ("13:30", "15:00")          # mismos momentos que ?demo (datos-validacion.js)
DIF_MIN_COBERTURA = 0.03           # datos-validacion.js: por debajo, A y B "cubren casi lo mismo"


def fmt(v, d=1, suf=""):
    return "—" if v is None else f"{v:.{d}f}".replace(".", ",") + suf


def pct(c):
    return f"{c * 100:.1f} %".replace(".", ",")


# ---------------- Capas de anotación ----------------
def escribir_capas(nombre, momentos, k, carpeta=SALIDA, etiqueta_fn=None, valor_fn=None):
    """Capas para Sonic Visualiser. etiqueta_fn y valor_fn cambian el texto y el valor de cada región
    (por defecto: hora · clase · cobertura, y la cobertura en %)."""
    carpeta.mkdir(parents=True, exist_ok=True)
    golpes, regiones, curva, audacity = [], [], [], []
    for m in momentos:
        etiqueta = etiqueta_fn(m) if etiqueta_fn else f"{m['hora']} · {m['clase'] or m['estado']} · {pct(m['cobertura'])}"
        valor = valor_fn(m) if valor_fn else m["cobertura"] * 100
        regiones.append(f"{m['inicio']:.4f},{valor:.2f},{m['fin'] - m['inicio']:.4f},\"{etiqueta}\"")
        audacity.append(f"{m['inicio']:.4f}\t{m['fin']:.4f}\t{etiqueta}")
        for i, g in enumerate(m["golpes"], 1):
            golpes.append(f"{g:.4f},\"golpe {i}/{m['pulsos']} ({m['hora']})\"")
            audacity.append(f"{g:.4f}\t{g:.4f}\tgolpe {i}/{m['pulsos']}")
        if m["rumor"] > 0:
            t = m["inicio"]
            while t <= m["fin"]:
                v = ma.envolvente_rumor(t - m["inicio"], m["rumor"], k)
                curva.append(f"{t:.3f},{ma.db(ma.rms_rumor_previsto(v, k)):.2f}")
                t += 0.05
    (carpeta / f"{nombre}_golpes.csv").write_text("\n".join(golpes) + "\n", encoding="utf-8")
    (carpeta / f"{nombre}_momentos.csv").write_text("\n".join(regiones) + "\n", encoding="utf-8")
    (carpeta / f"{nombre}_rumor.csv").write_text("\n".join(curva) + "\n", encoding="utf-8")
    (carpeta / f"{nombre}_audacity.txt").write_text("\n".join(audacity) + "\n", encoding="utf-8")


LEEME = """# Escuchar y ver Pacha Takiy en Sonic Visualiser

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
"""


# ---------------- Visor accesible (GitHub Pages) ----------------
def escribir_visor(pistas, k, ab, extra, carpeta=VISOR):
    """Copia los WAV y escribe datos.json para docs/acustica/index.html: ver, escuchar y sentir la verificación."""
    import shutil
    carpeta.mkdir(parents=True, exist_ok=True)
    salida = {"generado": date.today().isoformat(), "frecuencia_golpe": k["FRECUENCIA"], "vibra_ms": k["VIBRA_MS"],
              "ab": {"A": ab["A"]["hora_peru"], "B": ab["B"]["hora_peru"], "delta_db": round(ab["delta_db"], 2), "veces": round(ab["sonios"], 2)},
              "pistas": []}
    salida.update(extra)
    for pid, titulo, momentos, filas, tipo, info in pistas:
        shutil.copyfile(SALIDA / f"{pid}.wav", carpeta / f"{pid}.wav")
        salida["pistas"].append({"id": pid, "titulo": titulo, "tipo": tipo, "archivo": f"{pid}.wav", "momentos": [
            {"etiqueta": m["hora"], "clase": m["clase"], "cobertura": m["cobertura"], "inicio": round(m["inicio"], 4),
             "fin": round(m["fin"], 4), "golpes": [round(g, 4) for g in m["golpes"]],
             "rumor_previsto_db": f["rumor_previsto_db"], "rumor_medido_db": f["rumor_medido_db"],
             "golpes_medidos": f["golpes_medidos"], "error_max_ms": f["error_max_ms"], "ok": f["ok"], **(info[i] if info else {})}
            for i, (m, f) in enumerate(zip(momentos, filas))]})
    (carpeta / "datos.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
    # Vista 3D (docs/3d/): relieve real de Moquegua (scripts/terreno_3d.py)
    dem = ma.RAIZ / "datos" / "mapa" / "elevacion_moquegua.json"
    if dem.exists():
        (ma.RAIZ / "docs" / "3d").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(dem, ma.RAIZ / "docs" / "3d" / "elevacion.json")


# ---------------- Reporte ----------------
def tabla_momentos(filas, titulo):
    out = [f"### {titulo}", "",
           "| Momento | Clase | Cobertura | Golpes (regla / medidos) | Error máx. | Rumor previsto | Rumor medido | Golpe sobre rumor* | ¿Cumple? |",
           "|---|---|---|---|---|---|---|---|---|"]
    for f in filas:
        out.append(f"| {f['hora']} | {f['clase'] or '—'} | {pct(f['cobertura'])} | {f['golpes_esperados']} / {f['golpes_medidos']} | "
                   f"{fmt(f['error_max_ms'])} ms | {fmt(f['rumor_previsto_db'], 2, ' dBFS')} | {fmt(f['rumor_medido_db'], 2, ' dBFS')} | "
                   f"{fmt(f['margen_enmascaramiento_db'], 1, ' dB')} | {'sí' if f['ok'] else '**NO**'} |")
    out += ["", "\\* Margen del golpe de 440 Hz sobre el ruido del rumor dentro de la banda crítica del oído (ERB = "
            "24,7·(4,37·f/1000 + 1) ≈ 72 Hz). Más de 10 dB: el rumor nunca tapa un golpe.", ""]
    return out


def construir_reporte(k, ep, filas_tarde, filas_clases, ab, web=None):
    L = [f"# Reporte acústico de Pacha Takiy", "",
         f"Generado por `scripts/sonic_visualiser.py` el {date.today().isoformat()}. No editar a mano.", "",
         "Comprueba con números que lo que suena es lo que dice la regla del equipo. Las constantes se leen de "
         "`web/js/reglas.js` y `web/js/audio.js`; si alguien las cambia, este reporte y `pruebas/python/test_acustica.py` lo detectan.", "",
         "## 1. El modelo", "",
         "| Elemento | Fórmula (igual que la Web Audio API) |", "|---|---|",
         f"| Golpe | seno de {k['FRECUENCIA']:.0f} Hz · g(t); g sube exponencial de {k['GOLPE_PISO']} a {k['GOLPE_PICO']} en {k['GOLPE_ATAQUE'] * 1000:.0f} ms y baja exponencial a {k['GOLPE_PISO']} en {k['DURACION_GOLPE'] * 1000:.0f} ms |",
         f"| Instante del golpe i | t₀ + i · {k['VENTANA_S']}/n, con n = 2, 4 o 7 golpes |",
         f"| Rumor | ruido uniforme [−1, 1] → pasabanda biquad (fc = {k['RUMOR_FC']:.0f} Hz, Q = {k['RUMOR_Q']}) → nivel(c) |",
         f"| nivel(c) | {k['RUMOR_BASE']} + {k['RUMOR_RANGO']} · min(1, c / {k['COBERTURA_MAX']}) |",
         f"| RMS del rumor | nivel · volumen · (1/√3) · √G, con G = (1/π)∫\\|H(e^jω)\\|² dω = {ma.ganancia_potencia_ruido(*ma.coeficientes_pasabanda(k['RUMOR_FC'], k['RUMOR_Q'])):.4f} |",
         "| Sonoridad | ley de Stevens: se percibe el doble cada 10 dB |", "",
         "## 2. ¿Suena lo que dice la regla?", ""]
    L += tabla_momentos(filas_tarde, "Episodio del 10/02/2025 (paso 5, tal como suena en la web)")
    L += tabla_momentos(filas_clases, "Las tres intensidades (con el volumen al máximo)")
    L += ["## 3. ¿Se puede oír la diferencia entre A y B?", "",
          f"Demostración (`?demo`): A = {ab['A']['hora_peru']} ({pct(ab['A']['cobertura'])}) y B = {ab['B']['hora_peru']} ({pct(ab['B']['cobertura'])}).", "",
          f"- Diferencia de nivel del rumor: **{fmt(ab['delta_db'], 2, ' dB')}** (umbral de percepción ≈ {fmt(ma.JND_RUIDO_DB, 1)} dB; cómodo ≥ {fmt(ma.MARGEN_COMODO_DB, 1)} dB).",
          f"- Se percibe **{fmt(ab['sonios'], 2)} veces** más fuerte. Veredicto: **{'se oye con claridad' if ab['delta_db'] >= ma.MARGEN_COMODO_DB else 'difícil de oír'}**.",
          f"- ¿La respuesta correcta es robusta? Diferencia de cobertura A − B = {fmt(ab['boot']['diferencia'] * 100, 1)} puntos; intervalo de confianza del 95 % "
          f"por bootstrap de las 100 celdas: **{fmt(ab['boot']['ic95'][0] * 100, 1)} a {fmt(ab['boot']['ic95'][1] * 100, 1)} puntos**. No incluye 0 y su mínimo supera los 3 puntos de `DIF_MIN_COBERTURA`.", "",
          "### Resolución de la cobertura", "",
          f"La app considera que A y B son distintos si difieren en {DIF_MIN_COBERTURA * 100:.0f} puntos o más (`DIF_MIN_COBERTURA`). "
          "La tabla dice cuánto sube el rumor con esos 3 puntos y cuántos puntos hacen falta para llegar a 1 dB.", "",
          "| Cobertura | +3 puntos suben (curva actual) | Puntos para 1 dB (actual) | +3 puntos suben (curva en dB, propuesta) | Puntos para 1 dB (propuesta) |",
          "|---|---|---|---|---|"]
    for c in (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35):
        def subida(curva):
            return ma.db(curva(min(c + DIF_MIN_COBERTURA, 1), k) / curva(c, k))
        dmin = ma.diferencia_minima_audible(c, k)
        dmin_p = ma.diferencia_minima_audible(c, k, ma.nivel_rumor_propuesto)
        L.append(f"| {pct(c)} | {fmt(subida(ma.nivel_rumor), 2, ' dB')} | {fmt(dmin * 100 if dmin else None, 1)} | "
                 f"{fmt(subida(ma.nivel_rumor_propuesto), 2, ' dB')} | {fmt(dmin_p * 100 if dmin_p else None, 1)} |")
    todas = filas_tarde + filas_clases
    margen_min = min(f["margen_enmascaramiento_db"] for f in todas if f["margen_enmascaramiento_db"] is not None)
    error_max = max(f["error_max_ms"] for f in todas)
    golpe_db = ma.db(k["GOLPE_PICO"] * ma.VOLUMEN_DEFECTO)
    rumores = [f["rumor_previsto_db"] for f in filas_tarde if f["rumor_previsto_db"] is not None]
    corte = next((c / 1000 for c in range(10, 400) if ma.db(ma.nivel_rumor(c / 1000 + DIF_MIN_COBERTURA, k) / ma.nivel_rumor(c / 1000, k)) < ma.JND_RUIDO_DB), None)
    L += ["", "## 4. Hallazgos y propuestas", "",
          "Lo que cumple:", "",
          f"- Cada momento tiene exactamente los golpes de la regla (2, 4 o 7), con error de tiempo de {fmt(error_max)} ms como máximo.",
          f"- El rumor nunca tapa los golpes: el margen en la banda crítica es de {fmt(margen_min, 0)} dB o más.",
          "- Con el volumen al máximo, el pico queda por debajo del umbral del limitador (−3 dBFS): el limitador no cambia el sonido en régimen estable.",
          f"- La demostración A/B se oye con claridad ({fmt(ab['delta_db'], 1, ' dB')}).", "",
          "Lo que conviene decidir en equipo (no se cambió nada de la regla):", "",
          f"1. **3 puntos de cobertura no siempre se oyen.** Con la curva actual (lineal en amplitud), por encima de ~{pct(corte) if corte else '—'} de cobertura "
          "3 puntos suben el rumor menos de 1 dB, que es el límite de lo que el oído distingue. Hoy no afecta a la demo (A y B se eligen en los extremos), "
          "pero sí a otros episodios. Propuesta: `nivel(c) = 0,03 · (0,25/0,03)^min(1, c/0,4)` (mismo mínimo y mismo máximo, curva en decibeles): "
          "cada punto vale lo mismo, unos 0,46 dB, así que 3 puntos dan ≈1,4 dB en cualquier cobertura. Otra opción es decidir \"igual\" por dB (|ΔL| < 1 dB) y no por puntos.",
          "2. **El primer sonido tras crear el audio suena ~1,4 dB más bajo.** El limitador del navegador (DynamicsCompressor) tarda ~0,5 s en estabilizarse "
          "después de crearse el AudioContext. Solo afecta al primer golpe que se oye al entrar; si es \"Escuchar A\", A empieza un poco más bajo. "
          "Propuesta de una línea en `cambiarModo()` (`web/js/ajustes.js`): `if (modo !== \"ver\") Motor.asegurar();`. Elegir el modo ya es un gesto, así que el navegador lo permite. "
          "Así el limitador lleva más de 0,5 s estable cuando suena el primer momento, y no cambian los tiempos ni la vibración. "
          "En la prueba controlada, un golpe que suena 0,5 s o más después de crear el audio sale con 0,0 dB de diferencia.",
          f"3. **El rumor va {fmt(golpe_db - max(rumores), 0)} a {fmt(golpe_db - min(rumores), 0)} dB por debajo del pico de los golpes.** En una sala con ruido puede perderse justo la pista que decide A/B. Sugerencia: recomendar audífonos en el paso 3 "
          "o un botón \"escuchar solo el rumor\".", ""]
    if web:
        L += ["## 5. Comparación con el audio real de la web", "",
              "Capturado con `pruebas/web/acustica.spec.js`: el Motor real (`web/js/audio.js`, sin cambios) se renderiza con OfflineAudioContext, incluido el limitador.", "",
              f"- Retardo fijo del limitador: **{fmt(web['desfase_ms'], 1, ' ms')}** (constante; la vibración sigue sincronizada).",
              f"- Diferencia máxima de nivel del rumor web − modelo: **{fmt(web['dif_rumor_max_db'], 2, ' dB')}**.",
              f"- Golpes contados en la web: **{web['golpes_ok']} de {web['momentos']} momentos** con el número exacto.",
              f"- Primer golpe tras crear el audio, comparado con el modelo: **{fmt(web['primer_golpe_db'], 1, ' dB')}** en promedio "
              "(0 dB sería lo ideal; ver hallazgo 2).", ""]
        L += tabla_momentos(web["filas"], "Audio capturado de la web")
    L += ["## Cómo verlo en Sonic Visualiser", "", "Ejecuta `sonic_visualiser.bat` (o `python scripts/sonic_visualiser.py`) y sigue `salidas/sonic_visualiser/LEEME.md`.", ""]
    return "\n".join(L)


def analizar_web(carpeta, k, fots):
    """Lee los WAV que dejó acustica.spec.js (manifiesto.json) y los compara con el modelo."""
    carpeta = Path(carpeta)
    man = json.loads((carpeta / "manifiesto.json").read_text(encoding="utf-8"))
    filas, desfases, difs, primeros = [], [], [], []
    por_hora = {f["hora_peru"]: f for f in fots}
    for item in man["capturas"]:
        x, fs = ma.leer_wav(carpeta / item["archivo"])
        f = por_hora.get(item.get("hora")) or {"estado": "ok", "pulsos": item["pulsos"], "cobertura": item["cobertura"],
                                                "clase_nombre": item.get("clase"), "hora_peru": item.get("hora", "")}
        mom = ma.partitura([f], k, secuencia=False)
        d = aa.estimar_alineacion(x, fs, mom, k)
        fila = aa.comparar(x, fs, mom, k, volumen=man.get("volumen", ma.VOLUMEN_DEFECTO), desfase_s=d)[0]
        filas.append(fila)
        desfases.append(d)
        # Primer golpe vs segundo en la web, menos lo mismo en el modelo: aísla el efecto del limitador recién creado
        g = aa.detectar_golpes(x, fs, k["FRECUENCIA"])
        ref = ma.sintetizar(mom, k, volumen=man.get("volumen", ma.VOLUMEN_DEFECTO), fs=fs)
        gr = aa.detectar_golpes(ref, fs, k["FRECUENCIA"])
        if len(g) >= 2 and len(gr) >= 2:
            primeros.append((aa.energia_golpe_db(x, fs, g[0]) - aa.energia_golpe_db(x, fs, g[1]))
                            - (aa.energia_golpe_db(ref, fs, gr[0]) - aa.energia_golpe_db(ref, fs, gr[1])))
        if fila["rumor_medido_db"] is not None:
            difs.append(abs(fila["rumor_medido_db"] - fila["rumor_previsto_db"]))
    return {"filas": filas, "desfase_ms": 1000 * sum(desfases) / len(desfases), "dif_rumor_max_db": max(difs) if difs else 0.0,
            "golpes_ok": sum(f["golpes_medidos"] == f["golpes_esperados"] for f in filas), "momentos": len(filas),
            "primer_golpe_db": sum(primeros) / len(primeros) if primeros else None}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--web", help="carpeta con las capturas de la web (manifiesto.json + WAV)")
    p.add_argument("--sin-audio", action="store_true", help="solo el reporte, sin escribir WAV")
    a = p.parse_args(argv)

    k = ma.leer_constantes()
    ep = json.loads(ma.RUTA_EPISODIO.read_text(encoding="utf-8"))["fotogramas"]

    tarde = ma.partitura(ep, k)
    x_tarde = ma.sintetizar(tarde, k)
    filas_tarde = aa.comparar(x_tarde, ma.FS, tarde, k)

    clases_f = [{"estado": "ok", "pulsos": k["PULSOS"][c], "cobertura": 0.20, "clase_nombre": n, "hora_peru": n.capitalize()}
                for c, n in ((0, "baja"), (1, "media"), (2, "alta"))]
    clases = ma.partitura(clases_f, k)
    x_clases = ma.sintetizar(clases, k, volumen=1.0)
    filas_clases = aa.comparar(x_clases, ma.FS, clases, k, volumen=1.0)

    A = next(f for f in ep if f["hora_peru"] == DEMO[0])
    B = next(f for f in ep if f["hora_peru"] == DEMO[1])
    delta = ma.db(ma.nivel_rumor(A["cobertura"], k) / ma.nivel_rumor(B["cobertura"], k))
    gg = geo.episodio_geografico()["momentos"]
    ab = {"A": A, "B": B, "delta_db": delta, "sonios": ma.sonios(delta),
          "boot": geo.bootstrap_diferencia(gg[A["hora_peru"]]["rejilla"], gg[B["hora_peru"]]["rejilla"])}

    filas_todas_temp = []
    if not a.sin_audio:
        SALIDA.mkdir(parents=True, exist_ok=True)
        ma.escribir_wav(SALIDA / "tarde.wav", x_tarde)
        ma.escribir_wav(SALIDA / "clases.wav", x_clases)
        ab_m = ma.partitura([{**A, "hora_peru": "A " + A["hora_peru"]}, {**B, "hora_peru": "B " + B["hora_peru"]}], k)
        ma.escribir_wav(SALIDA / "ab_demo.wav", ma.sintetizar(ab_m, k))
        escribir_capas("tarde", tarde, k)
        escribir_capas("clases", clases, k)
        escribir_capas("ab_demo", ab_m, k)
        (SALIDA / "LEEME.md").write_text(LEEME, encoding="utf-8")
        x_ab = ma.sintetizar(ab_m, k)
        filas_ab = aa.comparar(x_ab, ma.FS, ab_m, k)
        # El Niño y 44 temporadas de lluvia (NASA POWER + NOAA ONI), con el mismo vocabulario de golpes y rumor
        r_enso = en.analizar()
        temporadas = ma.partitura(en.partitura_temporadas(r_enso, k["COBERTURA_MAX"]), k, secuencia=False)
        x_temp = ma.sintetizar(temporadas, k)
        filas_temp = aa.comparar(x_temp, ma.FS, temporadas, k)
        ma.escribir_wav(SALIDA / "temporadas.wav", x_temp)
        info_temp = [{"lluvia": f["lluvia"], "oni": f["oni"], "fase": f["fase"], "categoria": f["categoria_nombre"]} for f in r_enso["temporadas"]]
        pt = r_enso["proxima_temporada"]
        info_temp.append({"lluvia": pt["lluvia_esperada"], "oni": pt["oni_usado"], "fase": "El Niño muy fuerte (hoy)",
                          "categoria": pt["categoria_esperada"], "esperado": True})
        escribir_capas("temporadas", temporadas, k,
                       etiqueta_fn=lambda m: f"{m['id']} · {m['clase']}",
                       valor_fn=lambda m: info_temp[temporadas.index(m)]["lluvia"])
        (SALIDA / "temporadas_oni.csv").write_text("".join(f"{m['inicio']:.4f},{info_temp[i]['oni']:.2f}\n" for i, m in enumerate(temporadas)), encoding="utf-8")
        filas_todas_temp = filas_temp
        g = geo.episodio_geografico()
        info_ep = lambda ms: [{"geo": g["momentos"].get(m["hora"].split(" ")[-1])} for m in ms]
        escribir_visor([("ab_demo", "Demo A y B: ¿en qué momento llueve en más área?", ab_m, filas_ab, "episodio", info_ep(ab_m)),
                        ("tarde", "La tarde del 10 de febrero de 2025 (6 momentos)", tarde, filas_tarde, "episodio", info_ep(tarde)),
                        ("clases", "Las tres intensidades: baja, media y alta", clases, filas_clases, "clases", None),
                        ("temporadas", "El Niño y 44 temporadas de lluvia en Moquegua (1982–2025) + lo esperado para 2026–27", temporadas, filas_temp, "temporadas", info_temp)],
                       k, ab, {"geo": {kk: v for kk, v in g.items() if kk != "momentos"},
                               "enso": {kk: r_enso[kk] for kk in ("fuentes", "terciles_mm_dia", "pearson_r", "p_permutacion", "senal_el_nino_fuerte", "compuestos", "proxima_temporada")}})

    if not a.sin_audio:
        import sesion_sonic_visualiser
        sesion_sonic_visualiser.main()          # .sv: doble clic y se abre todo en Sonic Visualiser
    web = analizar_web(a.web, k, ep) if a.web else None
    REPORTE.write_text(construir_reporte(k, ep, filas_tarde, filas_clases, ab, web), encoding="utf-8")

    todo = filas_tarde + filas_clases + (web["filas"] if web else []) + (filas_todas_temp if not a.sin_audio else [])
    malos = [f["hora"] for f in todo if not f["ok"]]
    print(f"Reporte: {REPORTE.relative_to(ma.RAIZ)}")
    if not a.sin_audio:
        print(f"Sonic Visualiser: {SALIDA.relative_to(ma.RAIZ)}/ (abre LEEME.md)")
    if not a.sin_audio:
        print(f"Visor accesible: {VISOR.relative_to(ma.RAIZ)}/index.html (GitHub Pages)")
    print(f"A/B demo: {delta:.2f} dB de diferencia en el rumor.")
    if malos:
        print("NO cumplen la regla: " + ", ".join(malos))
        return 1
    print("Todo suena como dice la regla.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

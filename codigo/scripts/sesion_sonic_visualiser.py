"""
Pacha Takiy: sesiones de Sonic Visualiser (.sv) que abren todo con doble clic.

Cada sesión carga el WAV con su espectrograma (escala logarítmica, 100–6000 Hz) y las capas:
golpes (instantes), momentos o temporadas (regiones con su valor), curva del rumor (dBFS) y,
en El Niño, la curva del ONI de NOAA en un panel aparte. El .sv busca el WAV en la misma carpeta.

Uso: python scripts/sesion_sonic_visualiser.py   (después de sonic_visualiser.py)
"""
import bz2
import csv
import wave
from pathlib import Path
from xml.sax.saxutils import quoteattr

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "salidas" / "sonic_visualiser"


def _leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return [fila for fila in csv.reader(f) if fila]


def _con_silencios(filas, piso=-70.0):
    """La curva baja al piso entre momentos (si no, Sonic Visualiser une con una recta el final de uno y el inicio del otro)."""
    out, prev = [], None
    for t, v in filas:
        t, v = float(t), max(piso, float(v))
        if prev is not None and t - prev > 0.2:
            out += [(f"{prev + 0.05:.3f}", f"{piso:.2f}"), (f"{t - 0.05:.3f}", f"{piso:.2f}")]
        out.append((f"{t:.3f}", f"{v:.2f}"))
        prev = t
    return out


def sesion(nombre, titulo, curvas_extra=()):
    """Escribe salidas/sonic_visualiser/<nombre>.sv. curvas_extra: [(archivo_csv, nombre, unidades)] en paneles aparte."""
    wav = CARPETA / f"{nombre}.wav"
    with wave.open(str(wav)) as w:
        fs, n = w.getframerate(), w.getnframes()
    fr = lambda t: int(round(float(t) * fs))
    golpes = _leer(CARPETA / f"{nombre}_golpes.csv")
    regiones = _leer(CARPETA / f"{nombre}_momentos.csv")
    rumor = _con_silencios(_leer(CARPETA / f"{nombre}_rumor.csv"))
    curvas = [("rumor", "Rumor previsto", "dBFS", rumor)] + [(a, b, u, _leer(CARPETA / a)) for a, b, u in curvas_extra]

    x = ['<?xml version="1.0" encoding="UTF-8"?>', "<!DOCTYPE sonic-visualiser>", "<sv>", "<data>",
         f'  <model id="1" name={quoteattr(wav.name)} sampleRate="{fs}" start="0" end="{n}" type="wavefile" file={quoteattr(wav.name)} mainModel="true"/>']
    # Golpes: instantes
    x.append(f'  <model id="2" name="Golpes (regla)" sampleRate="{fs}" start="0" end="{n}" type="sparse" dimensions="1" resolution="1" notifyOnAdd="true" dataset="3"/>')
    x.append('  <dataset id="3" dimensions="1">')
    x += [f'    <point frame="{fr(t)}" label={quoteattr(et)}/>' for t, et in golpes]
    x.append("  </dataset>")
    # Momentos o temporadas: regiones
    vals = [float(v) for _, v, _, _ in regiones]
    unidad = "mm/día" if nombre == "temporadas" else "% área"
    x.append(f'  <model id="4" name="Momentos" sampleRate="{fs}" start="0" end="{n}" type="sparse" dimensions="3" resolution="1" notifyOnAdd="true" dataset="5" '
             f'subtype="region" valueQuantization="0" minimum="0" maximum="{max(vals) * 1.1:.3f}" units={quoteattr(unidad)}/>')
    x.append('  <dataset id="5" dimensions="3">')
    x += [f'    <point frame="{fr(t)}" value="{float(v):.3f}" duration="{fr(d)}" label={quoteattr(et)}/>' for t, v, d, et in regiones]
    x.append("  </dataset>")
    # Curvas (rumor, ONI): tiempo-valor
    ids = []
    sig = 6
    for archivo, nom, unidades, filas in curvas:
        vv = [float(v) for _, v in filas]
        mid, did = sig, sig + 1
        x.append(f'  <model id="{mid}" name={quoteattr(nom)} sampleRate="{fs}" start="0" end="{n}" type="sparse" dimensions="2" resolution="1" notifyOnAdd="true" '
                 f'dataset="{did}" minimum="{min(vv) - 0.1 * (max(vv) - min(vv)):.3f}" maximum="{max(vv) + 0.15 * (max(vv) - min(vv)):.3f}" units={quoteattr(unidades)}/>')
        x.append(f'  <dataset id="{did}" dimensions="2">')
        x += [f'    <point frame="{fr(t)}" value="{float(v):.3f}" label=""/>' for t, v in filas]
        x.append("  </dataset>")
        ids.append((mid, nom))
        sig += 2
    capa = sig
    L = {"regla": capa, "onda": capa + 1, "espectro": capa + 2, "golpes": capa + 3, "momentos": capa + 4}
    x += [f'  <layer id="{L["regla"]}" type="timeruler" name="Regla" model="1" colourName="Bright Orange" colour="#ffbc50" darkBackground="true"/>',
          f'  <layer id="{L["onda"]}" type="waveform" name="Onda" model="1" gain="1" showMeans="1" greyscale="0" channelMode="0" channel="-1" scale="0" aggressive="0" autoNormalize="0" colourName="Bright Blue" colour="#1e96ff" darkBackground="true"/>',
          f'  <layer id="{L["espectro"]}" type="spectrogram" name="Espectrograma" model="1" channel="-1" windowSize="1024" windowHopLevel="2" gain="1" threshold="0" '
          f'minFrequency="100" maxFrequency="6000" colourScale="2" colourScheme="6" colourRotation="0" frequencyScale="1" binDisplay="0" normalizeColumns="false" normalizeVisibleArea="false"/>',
          f'  <layer id="{L["golpes"]}" type="timeinstants" name="Golpes (regla)" model="2" plotStyle="0" colourName="Bright Green" colour="#00ff00" darkBackground="true"/>',
          f'  <layer id="{L["momentos"]}" type="regions" name="Momentos" model="4" verticalScale="0" plotStyle="0" colourName="Bright Yellow" colour="#ffff00" darkBackground="true"/>']
    curva_capas = []
    for i, (mid, nom) in enumerate(ids):
        lid = capa + 5 + i
        color = ("Bright Orange", "#ffbc50") if i == 0 else ("Bright Red", "#ff3c3c")
        x.append(f'  <layer id="{lid}" type="timevalues" name={quoteattr(nom)} model="{mid}" plotStyle="2" verticalScale="0" scaleMinimum="0" scaleMaximum="0" '
                 f'colourName="{color[0]}" colour="{color[1]}" darkBackground="true"/>')
        curva_capas.append((lid, nom, mid))
    x.append("</data>")
    zoom = max(64, int(n / 1400))
    centro = n // 2
    vista = lambda capas, alto: ([f'  <view centre="{centro}" zoom="{zoom}" followPan="1" followZoom="1" tracking="page" type="pane" centreLineVisible="0" height="{alto}">']
                                 + [f'    <layer id="{lid}" type="{t}" name={quoteattr(nm)} model="{m}" visible="true"/>' for lid, t, nm, m in capas] + ["  </view>"])
    x += ["<display>", '  <window width="1400" height="900"/>']
    x += vista([(L["regla"], "timeruler", "Regla", 1), (L["espectro"], "spectrogram", "Espectrograma", 1),
                (L["golpes"], "timeinstants", "Golpes (regla)", 2)], 420)
    for i, (lid, nom, mid) in enumerate(curva_capas):
        capas = [(L["regla"], "timeruler", "Regla", 1), (lid, "timevalues", nom, mid)]
        if i == 0:
            capas.append((L["momentos"], "regions", "Momentos", 4))
        x += vista(capas, 200)
    x += ["</display>", "<selections>", "</selections>", "</sv>"]
    destino = CARPETA / f"{nombre}.sv"
    destino.write_bytes(bz2.compress(("\n".join(x) + "\n").encode("utf-8")))   # Sonic Visualiser guarda y lee .sv con bzip2
    return destino


def main():
    hechas = [sesion("ab_demo", "Demo A/B"), sesion("tarde", "La tarde"), sesion("clases", "Intensidades"),
              sesion("temporadas", "El Niño", [("temporadas_oni.csv", "ONI de NOAA (El Niño)", "°C")])]
    for h in hechas:
        print(f"Sesión: {h.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()

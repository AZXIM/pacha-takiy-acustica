"""
Pacha Takiy: dónde llueve dentro de la zona de Moquegua (para el visor y para describirlo en palabras).

Cada fotograma IMERG de la app mide 100 × 100 píxeles = 10 × 10 celdas de 0,1° (10 píxeles por celda).
Para cada celda: fracción de píxeles con lluvia y clase mediana, con la MISMA regla de clasificacion.py.
Con eso se dibuja el mapa celda por celda y se describe hacia dónde se concentra la lluvia.
"""
import json
from collections import Counter
from pathlib import Path

from PIL import Image

import clasificacion as cl

RAIZ = Path(__file__).resolve().parent.parent
ZONA = cl.ZONA                         # oeste, sur, este, norte (1° × 1°)
CELDAS = 10


def rejilla(ruta_png, leyenda, exactos):
    """Lista de 10 filas (de norte a sur) × 10 columnas (de oeste a este): {"f": fracción con lluvia, "c": clase o None}."""
    with Image.open(ruta_png) as im:
        im = im.convert("RGBA")
        lado = im.width // CELDAS
        filas = []
        for fy in range(CELDAS):
            fila = []
            for fx in range(CELDAS):
                bloque = im.crop((fx * lado, fy * lado, (fx + 1) * lado, (fy + 1) * lado))
                c = cl.contar_imagen(bloque, leyenda, exactos)
                fila.append({"f": round(c["con_lluvia"] / (lado * lado), 3), "c": cl.clase_mediana(c["conteo"])})
            filas.append(fila)
    return filas


def describir(rej):
    """Frase corta: cuántas celdas tienen lluvia y hacia qué parte de la zona se concentra."""
    peso = [(fy, fx, c["f"]) for fy, fila in enumerate(rej) for fx, c in enumerate(fila) if c["f"] > 0]
    con = sum(1 for _, _, f in peso if f >= 0.5)
    if not peso:
        return "No llueve en ninguna celda de la zona."
    total = sum(f for _, _, f in peso)
    cy = sum(fy * f for fy, _, f in peso) / total          # 0 = norte, 9 = sur
    cx = sum(fx * f for _, fx, f in peso) / total          # 0 = oeste, 9 = este
    ns = "norte" if cy < 3.5 else "sur" if cy > 5.5 else ""
    eo = "este" if cx > 5.5 else "oeste" if cx < 3.5 else ""
    lugar = (ns + eo) if (ns and eo) else (ns or eo or "centro")
    lugar = {"norteeste": "noreste", "norteoeste": "noroeste", "sureste": "sureste", "suroeste": "suroeste"}.get(lugar, lugar)
    extra = " (cuenca alta, hacia Carumas)" if cy < 4.5 and cx > 4.5 else " (hacia la costa)" if cy > 5.5 and cx < 4.5 else ""
    return f"Llueve en {con} de {CELDAS * CELDAS} celdas; la lluvia se concentra al {lugar} de la zona{extra}."


def colores_clase(leyenda):
    """Un color representativo de la leyenda oficial de NASA GIBS por clase (líquida, color central del tramo)."""
    out = {}
    for k in (0, 1, 2):
        cs = [c for c in leyenda["colores"] if c["clase"] == k and c["fase"] == "liquida"]
        c = cs[len(cs) // 2]
        out[k] = f"#{c['r']:02x}{c['g']:02x}{c['b']:02x}"
    return out


def episodio_geografico():
    """Rejilla y descripción de cada momento del episodio, más lo necesario para dibujar el mapa."""
    ley, exactos = cl.cargar_leyenda()
    ep = json.loads((RAIZ / "datos" / "episodio_moquegua.json").read_text(encoding="utf-8"))
    mapa = json.loads((RAIZ / "datos" / "mapa" / "moquegua_provincias.json").read_text(encoding="utf-8"))
    momentos = {}
    for f in ep["fotogramas"]:
        r = rejilla(RAIZ / "datos" / f["imagen"], ley, exactos)
        momentos[f["hora_peru"]] = {"rejilla": r, "descripcion": describir(r)}
    return {"zona": [ZONA["oeste"], ZONA["sur"], ZONA["este"], ZONA["norte"]], "provincias": mapa["provincias"], "fuente_mapa": mapa["fuente"],
            "lugares": [{"nombre": "Moquegua", "lat": -17.19747, "lon": -70.93587}, {"nombre": "Torata", "lat": -17.077, "lon": -70.843},
                        {"nombre": "Carumas", "lat": -16.812, "lon": -70.694}, {"nombre": "Ilo", "lat": -17.64, "lon": -71.34}],
            "colores_clase": colores_clase(ley), "momentos": momentos}


def bootstrap_diferencia(rej_a, rej_b, n=10000, semilla=2026):
    """IC 95 % de la diferencia de cobertura A − B remuestreando las 100 celdas (pareadas, con reemplazo).
    Si el intervalo no incluye 0, la respuesta del paso 3 es robusta a qué celdas mire el satélite."""
    import random
    fa = [c["f"] for fila in rej_a for c in fila]
    fb = [c["f"] for fila in rej_b for c in fila]
    d = [a - b for a, b in zip(fa, fb)]
    rng, medias = random.Random(semilla), []
    for _ in range(n):
        m = [d[rng.randrange(len(d))] for _ in d]
        medias.append(sum(m) / len(m))
    medias.sort()
    return {"diferencia": round(sum(d) / len(d), 4), "ic95": [round(medias[int(0.025 * n)], 4), round(medias[int(0.975 * n)], 4)]}

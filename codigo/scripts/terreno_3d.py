"""
Pacha Takiy: relieve real de Moquegua para la vista 3D (docs/3d/).

Descarga 4 teselas de elevación "Terrarium" (AWS Terrain Tiles, zoom 8, ~600 m por píxel; fuentes:
NASA SRTM, GMTED2010 y ETOPO1), las decodifica con la fórmula oficial

    elevación (m) = R·256 + G + B/256 − 32768

y las remuestrea (bilineal, de Mercator a una rejilla de 0,01° en latitud y longitud) sobre
la región de Moquegua: lon −71,55 a −69,95 y lat −17,9 a −15,95. Guarda datos/mapa/elevacion_moquegua.json.

Uso: python scripts/terreno_3d.py               (necesita internet una vez)
     python scripts/terreno_3d.py --teselas CARPETA   (usa teselas ya descargadas: raw_X_Y.png o X_Y.png)
"""
import argparse
import base64
import io
import json
import math
import struct
import urllib.request
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "datos" / "mapa" / "elevacion_moquegua.json"
Z, X0, Y0 = 8, 77, 139                      # teselas 77–78 × 139–140
REGION = {"oeste": -71.55, "este": -69.95, "sur": -17.9, "norte": -15.95, "paso": 0.01}
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"


def tesela(x, y, carpeta=None):
    if carpeta:
        for nombre in (f"raw_{x}_{y}.png", f"{x}_{y}.png"):
            ruta = Path(carpeta) / nombre
            if ruta.exists():
                im = Image.open(ruta).convert("RGB")
                if im.size != (256, 256):              # captura de pantalla: recortar la tesela centrada
                    w, h = im.size
                    im = im.crop(((w - 256) // 2 + (w % 2 == 1), 368, (w - 256) // 2 + 256 + (w % 2 == 1), 624)) if h > 256 else im
                return im
    with urllib.request.urlopen(URL.format(z=Z, x=x, y=y), timeout=30) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")


def mosaico(carpeta=None):
    filas = [[0.0] * 512 for _ in range(512)]
    for dx in (0, 1):
        for dy in (0, 1):
            im = tesela(X0 + dx, Y0 + dy, carpeta)
            px = im.load()
            for j in range(256):
                for i in range(256):
                    r, g, b = px[i, j]
                    filas[dy * 256 + j][dx * 256 + i] = r * 256 + g + b / 256 - 32768
    return filas


def a_pixel(lat, lon):
    n = 2 ** Z
    x = (lon + 180) / 360 * n
    y = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n
    return (y - Y0) * 256, (x - X0) * 256


def bilineal(m, f, c):
    f0, c0 = int(f), int(c)
    df, dc = f - f0, c - c0
    v = lambda a, b: m[min(511, a)][min(511, b)]
    return (v(f0, c0) * (1 - df) * (1 - dc) + v(f0, c0 + 1) * (1 - df) * dc
            + v(f0 + 1, c0) * df * (1 - dc) + v(f0 + 1, c0 + 1) * df * dc)


def construir(carpeta=None):
    m = mosaico(carpeta)
    p = REGION["paso"]
    nlon = round((REGION["este"] - REGION["oeste"]) / p) + 1
    nlat = round((REGION["norte"] - REGION["sur"]) / p) + 1
    valores = []
    for j in range(nlat):                    # de norte a sur
        lat = REGION["norte"] - j * p
        for i in range(nlon):                # de oeste a este
            lon = REGION["oeste"] + i * p
            valores.append(int(round(bilineal(m, *a_pixel(lat, lon)))))
    datos = {
        "fuente": "AWS Terrain Tiles (Terrarium, zoom 8, ~600 m). Fuentes de elevación: NASA SRTM, GMTED2010 y ETOPO1.",
        "url": URL.replace("{z}/{x}/{y}", f"{Z}/{{77-78}}/{{139-140}}"),
        "formula": "elevación = R·256 + G + B/256 − 32768 (m); remuestreo bilineal",
        "region": REGION, "columnas": nlon, "filas": nlat, "unidades": "m",
        "int16_le_base64": base64.b64encode(struct.pack(f"<{len(valores)}h", *valores)).decode(),
        "control": {},
    }
    def en(lat, lon):
        i, j = round((lon - REGION["oeste"]) / p), round((REGION["norte"] - lat) / p)
        return valores[j * nlon + i]
    for nombre, lat, lon in (("Moquegua", -17.197, -70.936), ("Ilo", -17.64, -71.34), ("Torata", -17.077, -70.843),
                             ("Cuajone", -17.04, -70.71), ("Carumas", -16.812, -70.694), ("Volcán Ubinas", -16.355, -70.903)):
        datos["control"][nombre] = en(lat, lon)
    return datos


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--teselas", help="carpeta con las 4 teselas ya descargadas")
    args = a.parse_args()
    d = construir(args.teselas)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    print(f"{DESTINO.relative_to(RAIZ)}: {d['columnas']} × {d['filas']} puntos. Control: {d['control']}")


if __name__ == "__main__":
    main()

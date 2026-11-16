"""
Pacha Takiy: calibración climática de Moquegua con El Niño (ENSO) y datos de NASA.

Pregunta: con El Niño presente (ONI de NOAA), ¿cómo suele ser la temporada de lluvias en la cuenca alta de
Moquegua? Responde con 44 temporadas reales (dic–mar, 1982–2025) de NASA POWER (MERRA-2, PRECTOTCORR):

  1. Terciles climatológicos sobre la normal OMM 1991–2020: "bajo lo normal", "normal" y "sobre lo normal"
     (la misma forma de hablar que SENAMHI y NOAA en sus pronósticos estacionales).
  2. Relación lluvia–ONI: correlación de Pearson y de Spearman, regresión lineal y un valor p por permutación
     (20 000 permutaciones, sin suponer normalidad).
  3. ¿La calibración con El Niño acierta más que el promedio? Validación cruzada dejando una temporada fuera:
     porcentaje de aciertos del tercil frente al 33,3 % del azar, y puntaje de Heidke.
  4. Compuestos por fase (El Niño fuerte, El Niño, neutro, La Niña) y lo que la historia dice para 2026–27.
  5. Sonificación con el mismo vocabulario de la app: 2 / 4 / 7 golpes = bajo / normal / sobre lo normal, y el
     rumor de fondo crece con la lluvia de la temporada.

No es un pronóstico oficial: para eso están SENAMHI y ENFEN. Es la evidencia histórica de NASA para Moquegua.
"""
import json
import random
import statistics
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "datos" / "enso"
NORMAL = (1991, 2020)
CATEGORIAS = ("bajo lo normal", "normal", "sobre lo normal")
PULSOS_CATEGORIA = {0: 2, 1: 4, 2: 7}       # mismo vocabulario de la app: más golpes = más lluvia


def cargar():
    lluvia = json.loads((CARPETA / "power_moquegua_lluvias.json").read_text(encoding="utf-8"))
    oni = json.loads((CARPETA / "oni_noaa.json").read_text(encoding="utf-8"))
    return lluvia, oni


def temporadas(lluvia, oni):
    """Temporada Y = diciembre de Y-1 + enero, febrero y marzo de Y. Promedio en mm/día."""
    m, o = lluvia["meses_mm_dia"], oni["oni_djf"]
    filas = []
    for y in range(1982, 2026):
        a, b = m[str(y - 1)], m[str(y)]
        valores = [a["dic"], b["ene"], b["feb"], b["mar"]]
        filas.append({"anio": y, "etiqueta": f"{y - 1}-{str(y)[2:]}", "lluvia": round(sum(valores) / 4, 4),
                      "meses": valores, "oni": o[str(y)]})
    return filas


def fase(oni):
    if oni >= 1.5:
        return "El Niño fuerte"
    if oni >= 0.5:
        return "El Niño"
    if oni <= -0.5:
        return "La Niña"
    return "Neutro"


def percentil(xs, p):
    s = sorted(xs)
    k = (len(s) - 1) * p
    i = int(k)
    return s[i] + (s[min(i + 1, len(s) - 1)] - s[i]) * (k - i)


def terciles(filas):
    normal = [f["lluvia"] for f in filas if NORMAL[0] <= f["anio"] <= NORMAL[1]]
    return percentil(normal, 1 / 3), percentil(normal, 2 / 3)


def categoria(v, t):
    return 0 if v < t[0] else 2 if v > t[1] else 1


def pearson(x, y):
    mx, my = statistics.fmean(x), statistics.fmean(y)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    sx = sum((a - mx) ** 2 for a in x) ** 0.5
    sy = sum((b - my) ** 2 for b in y) ** 0.5
    return sxy / (sx * sy)


def rangos(x):
    orden = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[orden[j + 1]] == x[orden[i]]:
            j += 1
        for k in range(i, j + 1):
            r[orden[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def regresion(x, y):
    mx, my = statistics.fmean(x), statistics.fmean(y)
    b = sum((a - mx) * (c - my) for a, c in zip(x, y)) / sum((a - mx) ** 2 for a in x)
    return my - b * mx, b


def p_permutacion(x, y, n=20000, semilla=2026):
    """Valor p de dos colas: fracción de permutaciones con |r| >= |r observado|."""
    r0 = abs(pearson(x, y))
    rng, yy, mayores = random.Random(semilla), list(y), 0
    for _ in range(n):
        rng.shuffle(yy)
        if abs(pearson(x, yy)) >= r0 - 1e-12:
            mayores += 1
    return (mayores + 1) / (n + 1)


def validacion_cruzada(filas, t):
    """Deja una temporada fuera, ajusta lluvia = a + b·ONI con el resto y predice su tercil."""
    aciertos, tabla = 0, [[0] * 3 for _ in range(3)]
    for i, f in enumerate(filas):
        resto = [g for j, g in enumerate(filas) if j != i]
        a, b = regresion([g["oni"] for g in resto], [g["lluvia"] for g in resto])
        pred, obs = categoria(a + b * f["oni"], t), categoria(f["lluvia"], t)
        tabla[obs][pred] += 1
        aciertos += pred == obs
    n = len(filas)
    esperado = sum(sum(tabla[k]) * sum(tabla[j][k] for j in range(3)) for k in range(3)) / n
    heidke = (aciertos - esperado) / (n - esperado)
    return {"aciertos": aciertos, "n": n, "porcentaje": round(100 * aciertos / n, 1), "heidke": round(heidke, 3), "tabla": tabla}


def senal_el_nino_fuerte(filas, umbral=1.5):
    """Regla "ONI ≥ 1,5 → bajo lo normal", validada dejando una temporada fuera, y la probabilidad de
    obtener al menos ese número de temporadas secas por azar (binomial con p = 1/3)."""
    from math import comb
    fuertes = [f for f in filas if f["oni"] >= umbral]
    aciertos = 0
    for i, f in enumerate(fuertes):
        otros = [g["categoria"] for j, g in enumerate(fuertes) if j != i]
        moda = max(range(3), key=lambda k: (otros.count(k), -k))
        aciertos += moda == f["categoria"]
    n, k = len(fuertes), sum(f["categoria"] == 0 for f in fuertes)
    p_azar = sum(comb(n, j) * (1 / 3) ** j * (2 / 3) ** (n - j) for j in range(k, n + 1))
    return {"n": n, "bajo_lo_normal": k, "aciertos_loo": aciertos, "porcentaje_loo": round(100 * aciertos / n, 1),
            "p_azar": round(p_azar, 4)}


def analizar():
    lluvia, oni = cargar()
    filas = temporadas(lluvia, oni)
    t = terciles(filas)
    for f in filas:
        f["fase"] = fase(f["oni"])
        f["categoria"] = categoria(f["lluvia"], t)
        f["categoria_nombre"] = CATEGORIAS[f["categoria"]]
    x, y = [f["oni"] for f in filas], [f["lluvia"] for f in filas]
    a, b = regresion(x, y)
    residuos = [yy - (a + b * xx) for xx, yy in zip(x, y)]
    s = (sum(r * r for r in residuos) / (len(x) - 2)) ** 0.5
    compuestos = {}
    for nombre in ("El Niño fuerte", "El Niño", "Neutro", "La Niña"):
        g = [f for f in filas if f["fase"] == nombre or (nombre == "El Niño" and f["fase"] == "El Niño fuerte")]
        compuestos[nombre] = {"n": len(g), "lluvia_media": round(statistics.fmean([f["lluvia"] for f in g]), 3) if g else None,
                              "por_categoria": [sum(f["categoria"] == k for f in g) for k in range(3)],
                              "temporadas": [f["etiqueta"] for f in g]}
    oni_hoy = oni["ultimo"]["oni"]
    esperado = a + b * oni_hoy
    mx = statistics.fmean(x)
    sxx = sum((v - mx) ** 2 for v in x)
    error_pred = s * (1 + 1 / len(x) + (oni_hoy - mx) ** 2 / sxx) ** 0.5
    t90 = 1.682                                   # t de Student, 90 % de dos colas, 42 grados de libertad
    fuerte = compuestos["El Niño fuerte"]
    return {
        "fuentes": {"lluvia": lluvia["fuente"], "lluvia_consulta": lluvia["consulta"], "oni": oni["fuente"], "oni_consulta": oni["consulta"],
                    "fecha_acceso": lluvia["fecha_acceso"], "estado_actual": oni["estado_actual"], "celda": lluvia["celda_merra2"], "punto": lluvia["punto"]},
        "temporadas": filas,
        "terciles_mm_dia": [round(t[0], 3), round(t[1], 3)],
        "normal": list(NORMAL),
        "pearson_r": round(pearson(x, y), 3),
        "spearman_rho": round(pearson(rangos(x), rangos(y)), 3),
        "p_permutacion": round(p_permutacion(x, y), 4),
        "regresion": {"a": round(a, 4), "b": round(b, 4), "error_estandar": round(s, 4)},
        "validacion_cruzada": validacion_cruzada(filas, t),
        "senal_el_nino_fuerte": senal_el_nino_fuerte(filas),
        "compuestos": compuestos,
        "proxima_temporada": {
            "etiqueta": "2026-27", "oni_usado": oni_hoy, "oni_estacion": oni["ultimo"]["estacion"],
            "lluvia_esperada": round(esperado, 3),
            "intervalo_90": [round(max(0.0, esperado - t90 * error_pred), 3), round(esperado + t90 * error_pred, 3)],
            "categoria_esperada": CATEGORIAS[categoria(esperado, t)],
            "historia_el_nino_fuerte": f"{fuerte['por_categoria'][0]} de {fuerte['n']} temporadas con El Niño fuerte fueron bajo lo normal; "
                                       f"{fuerte['por_categoria'][2]} sobre lo normal.",
        },
    }


def partitura_temporadas(r, cobertura_max):
    """Fotogramas para modelo_acustico.partitura(): golpes por tercil, rumor proporcional a la lluvia."""
    tope = max(f["lluvia"] for f in r["temporadas"])
    fots = []
    for f in r["temporadas"]:
        fots.append({"estado": "ok", "pulsos": PULSOS_CATEGORIA[f["categoria"]], "clase_nombre": f["categoria_nombre"],
                     "cobertura": round(cobertura_max * f["lluvia"] / tope, 4), "hora_peru": f["etiqueta"],
                     "id": f"{f['etiqueta']} · {f['fase']} (ONI {f['oni']:+.2f})"})
    p = r["proxima_temporada"]
    cat = CATEGORIAS.index(p["categoria_esperada"])
    fots.append({"estado": "ok", "pulsos": PULSOS_CATEGORIA[cat], "clase_nombre": p["categoria_esperada"] + " (esperado)",
                 "cobertura": round(cobertura_max * p["lluvia_esperada"] / tope, 4), "hora_peru": "2026-27 (esperado)",
                 "id": f"2026-27 · El Niño muy fuerte (ONI {p['oni_usado']:+.2f})"})
    return fots


def fmt(v, d=2):
    return f"{v:.{d}f}".replace(".", ",")


def reporte(r):
    vc, p, c, sf = r["validacion_cruzada"], r["proxima_temporada"], r["compuestos"], r["senal_el_nino_fuerte"]
    L = ["# El Niño y la lluvia de Moquegua (calibración con datos de NASA)", "",
         "Generado por `scripts/enso_moquegua.py`. No editar a mano.", "",
         "## Datos", "",
         f"- Lluvia: {r['fuentes']['lluvia']}. Celda MERRA-2 de la cuenca alta (lat {r['fuentes']['celda']['sur']} a {r['fuentes']['celda']['norte']}, "
         f"lon {r['fuentes']['celda']['oeste']} a {r['fuentes']['celda']['este']}), dentro de la zona de 1° × 1° que usa la app.",
         f"- El Niño: {r['fuentes']['oni']}, estación DJF.",
         f"- Hoy: {r['fuentes']['estado_actual']['noaa']} {r['fuentes']['estado_actual']['enfen']}",
         f"- Temporada = diciembre a marzo, 44 temporadas (1981-82 a 2024-25). Consultado el {r['fuentes']['fecha_acceso']}.", "",
         "## Resultados", "",
         f"- **Terciles de la normal 1991–2020:** bajo lo normal si la temporada tiene menos de {fmt(r['terciles_mm_dia'][0])} mm/día; "
         f"sobre lo normal si tiene más de {fmt(r['terciles_mm_dia'][1])} mm/día.",
         f"- **Relación con El Niño:** Pearson r = {fmt(r['pearson_r'])}, Spearman ρ = {fmt(r['spearman_rho'])}, valor p por permutación = {fmt(r['p_permutacion'], 4)}. "
         f"Cada grado de ONI cambia la lluvia de la temporada en {fmt(r['regresion']['b'], 3)} mm/día.",
         f"- **¿Calibrar con El Niño acierta más?** En validación cruzada, el tercil se acierta en {vc['aciertos']} de {vc['n']} temporadas "
         f"({fmt(vc['porcentaje'], 1)} %, frente a 33,3 % del azar). Puntaje de Heidke: {fmt(vc['heidke'], 3)} (0 = azar, 1 = perfecto). "
         "Con todos los años mezclados, una recta casi no mejora el tercil: la señal no es pareja.",
         f"- **La señal está en los El Niño fuertes:** {sf['bajo_lo_normal']} de {sf['n']} fueron bajo lo normal. La regla \"ONI ≥ 1,5 → bajo lo normal\", "
         f"validada dejando una temporada fuera, acierta {sf['aciertos_loo']} de {sf['n']} ({fmt(sf['porcentaje_loo'], 0)} % frente a 33 % del azar). "
         f"La probabilidad de ver tantas temporadas secas por azar es {fmt(sf['p_azar'], 3)}. Esa es la calibración que importa hoy, con un El Niño muy fuerte.", "",
         "| Fase (ONI DJF) | Temporadas | Lluvia media (mm/día) | Bajo lo normal | Normal | Sobre lo normal |", "|---|---|---|---|---|---|"]
    for nombre, g in c.items():
        L.append(f"| {nombre} | {g['n']} | {fmt(g['lluvia_media'], 3)} | {g['por_categoria'][0]} | {g['por_categoria'][1]} | {g['por_categoria'][2]} |")
    L += ["", f"El Niño fuerte (ONI ≥ 1,5): {', '.join(c['El Niño fuerte']['temporadas'])}.", "",
          "## Temporada 2026–27", "",
          f"Con ONI {fmt(p['oni_usado'])} ({p['oni_estacion']}), la regresión espera **{fmt(p['lluvia_esperada'], 3)} mm/día** "
          f"(intervalo de 90 %: {fmt(p['intervalo_90'][0], 3)} a {fmt(p['intervalo_90'][1], 3)}), es decir **{p['categoria_esperada']}**. {p['historia_el_nino_fuerte']}", "",
          "Esto es evidencia histórica, no un pronóstico oficial. Para decisiones, usar los comunicados de ENFEN y los pronósticos de SENAMHI.", "",
          "## Cómo suena (Sonic Visualiser: `salidas/sonic_visualiser/temporadas.wav`)", "",
          "Una temporada por momento, con el mismo vocabulario de la app: **2 golpes = bajo lo normal, 4 = normal, 7 = sobre lo normal**. "
          "El rumor de fondo crece con la lluvia de la temporada. Las capas `temporadas_*.csv` marcan el año, la fase de El Niño y la curva del ONI.", "",
          "| Temporada | Lluvia (mm/día) | ONI DJF | Fase | Tercil |", "|---|---|---|---|---|"]
    for f in r["temporadas"]:
        L.append(f"| {f['etiqueta']} | {fmt(f['lluvia'], 3)} | {f['oni']:+.2f} | {f['fase']} | {f['categoria_nombre']} |")
    return "\n".join(L) + "\n"


def main():
    r = analizar()
    (CARPETA / "temporadas.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    (RAIZ / "pruebas" / "reportes" / "enso.md").write_text(reporte(r), encoding="utf-8")
    vc, p = r["validacion_cruzada"], r["proxima_temporada"]
    print(f"r = {r['pearson_r']}, p = {r['p_permutacion']}, aciertos LOO = {vc['porcentaje']} % (Heidke {vc['heidke']})")
    sf = r["senal_el_nino_fuerte"]
    print(f"El Niño fuerte: {sf['bajo_lo_normal']}/{sf['n']} bajo lo normal; LOO {sf['porcentaje_loo']} %; p azar {sf['p_azar']}")
    print(f"2026-27: {p['lluvia_esperada']} mm/día ({p['categoria_esperada']}); {p['historia_el_nino_fuerte']}")
    return r


if __name__ == "__main__":
    main()

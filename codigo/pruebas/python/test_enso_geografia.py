"""Pruebas de la calibración con El Niño (NASA POWER + NOAA ONI) y de la geografía de la lluvia."""
import json

import pytest

import enso_moquegua as en
import geografia as geo
import modelo_acustico as ma


@pytest.fixture(scope="module")
def r():
    return en.analizar()


# ---------- Datos ----------
def test_datos_completos_y_con_fuente():
    lluvia, oni = en.cargar()
    assert len(lluvia["meses_mm_dia"]) == 45 and "power.larc.nasa.gov" in lluvia["consulta"]
    assert all(set(m) == {"ene", "feb", "mar", "dic"} for m in lluvia["meses_mm_dia"].values())
    assert all(0 <= v < 5 for m in lluvia["meses_mm_dia"].values() for v in m.values())
    assert "cpc.ncep.noaa.gov" in oni["consulta"] and all(-3 < v < 3 for v in oni["oni_djf"].values())
    assert oni["oni_djf"]["1998"] == 2.22 and oni["oni_djf"]["2016"] == 2.50      # El Niño históricos


def test_temporada_es_diciembre_a_marzo():
    lluvia, oni = en.cargar()
    t = {f["anio"]: f for f in en.temporadas(lluvia, oni)}
    m = lluvia["meses_mm_dia"]
    assert t[1998]["lluvia"] == pytest.approx((m["1997"]["dic"] + m["1998"]["ene"] + m["1998"]["feb"] + m["1998"]["mar"]) / 4, abs=1e-4)
    assert len(t) == 44 and t[1998]["etiqueta"] == "1997-98"


# ---------- Calibración ----------
def test_terciles_reparten_la_normal_en_tres(r):
    normal = [f for f in r["temporadas"] if 1991 <= f["anio"] <= 2020]
    cuentas = [sum(f["categoria"] == k for f in normal) for k in range(3)]
    assert len(normal) == 30 and all(9 <= c <= 11 for c in cuentas)


def test_el_nino_reduce_la_lluvia_en_la_cuenca_alta(r):
    assert r["pearson_r"] < 0 and r["spearman_rho"] < 0
    assert r["p_permutacion"] < 0.05
    assert r["regresion"]["b"] < 0


def test_senal_de_el_nino_fuerte(r):
    sf = r["senal_el_nino_fuerte"]
    assert sf["n"] == 5 and sf["bajo_lo_normal"] >= 4
    assert sf["porcentaje_loo"] > 33.4 and sf["p_azar"] < 0.05


def test_proxima_temporada_con_el_nino(r):
    p = r["proxima_temporada"]
    assert p["oni_usado"] >= 1.5
    assert p["intervalo_90"][0] <= p["lluvia_esperada"] <= p["intervalo_90"][1]
    assert p["categoria_esperada"] == "bajo lo normal"


def test_sonificacion_de_temporadas_usa_el_vocabulario_de_la_app(r):
    k = ma.leer_constantes()
    fots = en.partitura_temporadas(r, k["COBERTURA_MAX"])
    assert len(fots) == 45
    assert {f["pulsos"] for f in fots} <= set(k["PULSOS"].values())
    assert all(0 < f["cobertura"] <= k["COBERTURA_MAX"] for f in fots)
    seca, humeda = min(fots[:-1], key=lambda f: f["cobertura"]), max(fots[:-1], key=lambda f: f["cobertura"])
    assert seca["pulsos"] == 2 and humeda["pulsos"] == 7


# ---------- Geografía ----------
def test_rejilla_coincide_con_el_episodio():
    g = geo.episodio_geografico()
    ep = json.loads((ma.RAIZ / "datos" / "episodio_moquegua.json").read_text(encoding="utf-8"))
    for f in ep["fotogramas"]:
        rej = g["momentos"][f["hora_peru"]]["rejilla"]
        assert len(rej) == 10 and all(len(fila) == 10 for fila in rej)
        cobertura = sum(c["f"] for fila in rej for c in fila) / 100
        assert cobertura == pytest.approx(f["cobertura"], abs=0.002)


def test_la_lluvia_del_episodio_esta_en_la_cuenca_alta():
    g = geo.episodio_geografico()
    for m in g["momentos"].values():
        assert "noreste" in m["descripcion"] and "Carumas" in m["descripcion"]


def test_describir_casos_simples():
    vacia = [[{"f": 0, "c": None}] * 10 for _ in range(10)]
    assert geo.describir(vacia).startswith("No llueve")
    sur = [[{"f": 1.0 if fy >= 8 else 0, "c": 0} for _ in range(10)] for fy in range(10)]
    assert "sur" in geo.describir(sur)


def test_respuesta_ab_robusta_por_bootstrap():
    g = geo.episodio_geografico()["momentos"]
    b = geo.bootstrap_diferencia(g["13:30"]["rejilla"], g["15:00"]["rejilla"])
    assert b["ic95"][0] > 0.03          # el mínimo plausible supera DIF_MIN_COBERTURA
    assert b["ic95"][0] <= b["diferencia"] <= b["ic95"][1]


# ---------- Relieve real para la vista 3D ----------
def test_relieve_de_moquegua_es_plausible():
    import base64
    import struct
    d = json.loads((ma.RAIZ / "datos" / "mapa" / "elevacion_moquegua.json").read_text(encoding="utf-8"))
    z = struct.unpack(f"<{d['columnas'] * d['filas']}h", base64.b64decode(d["int16_le_base64"]))
    assert len(z) == 161 * 196 and min(z) < 0 < 5000 < max(z)          # mar al oeste, Andes al este
    c = d["control"]
    assert 1200 < c["Moquegua"] < 1700 and c["Ilo"] < 200 and 2800 < c["Carumas"] < 3700 and c["Volcán Ubinas"] > 4500
    assert "SRTM" in d["fuente"]

"""Pruebas del modelo acústico: que lo que suena sea exactamente lo que dice la regla (y que se pueda oír)."""
import csv
import json
import re

import pytest

import analisis_acustico as aa
import clasificacion as cl
import modelo_acustico as ma
import sonic_visualiser as sv


@pytest.fixture(scope="module")
def k():
    return ma.leer_constantes()


@pytest.fixture(scope="module")
def episodio():
    return json.loads(ma.RUTA_EPISODIO.read_text(encoding="utf-8"))


def momento(pulsos, cobertura, nombre="m"):
    return {"estado": "ok", "pulsos": pulsos, "cobertura": cobertura, "clase_nombre": nombre, "hora_peru": nombre}


# ---------- Una sola fuente de verdad ----------
def test_constantes_iguales_en_python_js_y_episodio(k, episodio):
    assert k["PULSOS"] == cl.PULSOS
    assert k["VENTANA_S"] == episodio["metodo"]["ventana_pulsos_s"]
    assert k["SILENCIO_S"] == episodio["metodo"]["silencio_entre_fotogramas_s"]
    js = (ma.RAIZ / "web" / "js" / "datos-validacion.js").read_text(encoding="utf-8")
    assert float(re.search(r"DIF_MIN_COBERTURA = ([\d.]+)", js).group(1)) == sv.DIF_MIN_COBERTURA


def test_un_cambio_en_audio_js_se_detecta(tmp_path):
    original = ma.RUTA_AUDIO_JS.read_text(encoding="utf-8")
    cambiado = tmp_path / "audio.js"
    cambiado.write_text(original.replace("Math.min(1, cobertura / COBERTURA_MAX)", "Math.sqrt(cobertura)"), encoding="utf-8")
    with pytest.raises(ma.CambioEnAudioJS):
        ma.leer_constantes(audio=cambiado)


# ---------- La partitura ----------
@pytest.mark.parametrize("pulsos", [2, 4, 7])
def test_golpes_repartidos_en_la_ventana(k, pulsos):
    m = ma.partitura([momento(pulsos, 0.2)], k, secuencia=False)[0]
    assert len(m["golpes"]) == pulsos
    paso = k["VENTANA_S"] / pulsos
    assert all(abs((b - a) - paso) < 1e-9 for a, b in zip(m["golpes"], m["golpes"][1:]))
    assert m["golpes"][-1] + k["DURACION_GOLPE"] <= m["fin"]


def test_silencio_entre_golpes_permite_contarlos(k):
    paso_min = k["VENTANA_S"] / max(k["PULSOS"].values())
    assert paso_min - k["DURACION_GOLPE"] >= ma.SEPARACION_MIN_S


def test_sin_lluvia_o_ilegible_es_silencio(k):
    for estado in ("sin_precipitacion_visible", "ilegible", "sin_datos"):
        m = ma.partitura([{"estado": estado, "pulsos": 2, "cobertura": 0.0}], k, secuencia=False)[0]
        assert m["golpes"] == [] and m["rumor"] == 0


def test_rumor_crece_con_la_cobertura_y_se_satura(k):
    niveles = [ma.nivel_rumor(c / 100, k) for c in range(1, 60)]
    assert all(b >= a for a, b in zip(niveles, niveles[1:]))
    assert ma.nivel_rumor(k["COBERTURA_MAX"], k) == pytest.approx(k["RUMOR_BASE"] + k["RUMOR_RANGO"])
    assert ma.nivel_rumor(0.9, k) == ma.nivel_rumor(k["COBERTURA_MAX"], k)


# ---------- Síntesis + análisis: el oído automático ----------
@pytest.mark.parametrize("pulsos,cobertura", [(2, 0.05), (2, 0.25), (4, 0.3), (7, 0.4)])
def test_lo_que_suena_es_lo_que_dice_la_regla(k, pulsos, cobertura):
    mom = ma.partitura([momento(pulsos, cobertura)], k, secuencia=False)
    fila = aa.comparar(ma.sintetizar(mom, k), ma.FS, mom, k)[0]
    assert fila["golpes_medidos"] == pulsos
    assert fila["error_max_ms"] <= 1000 * aa.TOLERANCIA_TIEMPO_S
    assert fila["rumor_medido_db"] == pytest.approx(fila["rumor_previsto_db"], abs=1.0)


def test_episodio_completo_cumple(k, episodio):
    tarde = ma.partitura(episodio["fotogramas"], k)
    filas = aa.comparar(ma.sintetizar(tarde, k), ma.FS, tarde, k)
    assert [f["hora"] for f in filas if not f["ok"]] == []


def test_el_rumor_nunca_tapa_un_golpe(k):
    for c in (0.01, 0.1, 0.2, 0.3, k["COBERTURA_MAX"]):
        assert ma.margen_enmascaramiento_db(ma.nivel_rumor(c, k), k) >= ma.MARGEN_ENMASCARAMIENTO_DB


def test_el_peor_caso_no_activa_el_limitador(k):
    mom = ma.partitura([momento(7, k["COBERTURA_MAX"])], k, secuencia=False)
    assert aa.pico_dbfs(ma.sintetizar(mom, k, volumen=1.0)) < k["LIM_UMBRAL_DB"]


# ---------- ¿Se oye la diferencia? ----------
def test_demo_ab_se_oye_con_claridad(k, episodio):
    por_hora = {f["hora_peru"]: f for f in episodio["fotogramas"]}
    a, b = (por_hora[h] for h in sv.DEMO)
    assert ma.db(ma.nivel_rumor(a["cobertura"], k) / ma.nivel_rumor(b["cobertura"], k)) >= ma.MARGEN_COMODO_DB


def test_propuesta_curva_en_db_mantiene_extremos_y_hace_audibles_3_puntos(k):
    assert ma.nivel_rumor_propuesto(0.0001, k) == pytest.approx(k["RUMOR_BASE"], rel=1e-3)
    assert ma.nivel_rumor_propuesto(k["COBERTURA_MAX"], k) == pytest.approx(ma.nivel_rumor(k["COBERTURA_MAX"], k))
    for c in [i / 100 for i in range(1, 38)]:
        assert ma.db(ma.nivel_rumor_propuesto(c + sv.DIF_MIN_COBERTURA, k) / ma.nivel_rumor_propuesto(c, k)) >= ma.JND_RUIDO_DB


@pytest.mark.xfail(strict=True, reason="Hallazgo 1 (pruebas/reportes/acustica.md): con la curva actual, 3 puntos de "
                   "cobertura suben el rumor menos de 1 dB por encima de ~19 %. Pasará cuando el equipo adopte la curva en dB.")
def test_curva_actual_3_puntos_siempre_audibles(k):
    for c in [i / 100 for i in range(1, 38)]:
        assert ma.db(ma.nivel_rumor(c + sv.DIF_MIN_COBERTURA, k) / ma.nivel_rumor(c, k)) >= ma.JND_RUIDO_DB


# ---------- Archivos para Sonic Visualiser ----------
def test_wav_ida_y_vuelta(tmp_path):
    x = [0.0, 0.5, -0.5, 0.25] * 100
    ma.escribir_wav(tmp_path / "x.wav", x)
    y, fs = ma.leer_wav(tmp_path / "x.wav")
    assert fs == ma.FS and len(y) == len(x)
    assert max(abs(a - b) for a, b in zip(x, y)) < 1e-4


def test_capas_de_sonic_visualiser(k, episodio, tmp_path):
    tarde = ma.partitura(episodio["fotogramas"], k)
    sv.escribir_capas("tarde", tarde, k, carpeta=tmp_path)
    golpes = list(csv.reader((tmp_path / "tarde_golpes.csv").open(encoding="utf-8")))
    regiones = list(csv.reader((tmp_path / "tarde_momentos.csv").open(encoding="utf-8")))
    curva = list(csv.reader((tmp_path / "tarde_rumor.csv").open(encoding="utf-8")))
    assert len(golpes) == sum(m["pulsos"] for m in tarde)
    assert len(regiones) == len(tarde)
    assert all(len(r) == 4 and float(r[0]) >= 0 and float(r[2]) == pytest.approx(k["VENTANA_S"]) for r in regiones)
    assert [float(r[0]) for r in golpes] == sorted(float(r[0]) for r in golpes)
    assert all(len(r) == 2 for r in curva)
    lineas = (tmp_path / "tarde_audacity.txt").read_text(encoding="utf-8").splitlines()
    assert all(len(l.split("\t")) == 3 for l in lineas)


# ---------- Audio real de la web (lo deja pruebas/web/acustica.spec.js) ----------
CAPTURAS = ma.RAIZ / "pruebas" / "capturas" / "acustica"


@pytest.mark.skipif(not (CAPTURAS / "manifiesto.json").exists(), reason="Sin capturas de la web: corre primero npx playwright test acustica")
def test_audio_real_de_la_web_coincide_con_el_modelo(k, episodio):
    web = sv.analizar_web(CAPTURAS, k, episodio["fotogramas"])
    assert web["golpes_ok"] == web["momentos"]
    assert web["dif_rumor_max_db"] <= 0.5
    assert all(f["ok"] for f in web["filas"])
